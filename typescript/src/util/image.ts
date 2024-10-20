import * as path from 'path'
import * as fs from 'fs'
import { Readable, Stream } from 'stream'
import { ReadableStream as WebReadableStream } from 'stream/web'
import sharp from 'sharp'
import * as logging from '../util/_logging'

const logger = logging.getLogger('ell.image')

type URLString = string
type FilePath = string

type ImageFormat = 'png' | 'jpeg' | 'webp' | 'gif' | 'bmp' | 'tiff'

/**
 * Determines the image format from a base64 string
 * @param base64String The base64 string
 * @returns The image format
 */
export function imageFormatFromBase64(base64String: string): ImageFormat | null {
  // Extract only the first 16 characters,
  // which should be enough for the header
  const base64Header = base64String.slice(0, 16)

  // Decode the first part of the base64 to binary
  const binaryString = atob(base64Header)

  // Check the magic numbers in the binary string
  if (binaryString.startsWith('\xFF\xD8\xFF')) {
    return 'jpeg'
  } else if (binaryString.startsWith('\x89PNG\r\n\x1a\n')) {
    return 'png'
  } else if (binaryString.startsWith('GIF8')) {
    return 'gif'
  } else if (binaryString.startsWith('BM')) {
    return 'bmp'
  } else if (binaryString.startsWith('II*\x00') || binaryString.startsWith('MM\x00*')) {
    return 'tiff'
  } else if (binaryString.startsWith('RIFF') && binaryString.slice(8, 12) === 'WEBP') {
    return 'webp'
  } else {
    return null
  }
}

/**
 * Determines the image format from a buffer
 * @param buffer The image buffer
 * @returns The image format
 */
export function imageFormatFromBuffer(buffer: Buffer) {
  return imageFormatFromBase64(buffer.subarray(0, 16).toString('base64'))
}

type Source =
  | {
      type: 'file'
      path: string
    }
  | {
      type: 'url'
      url: URLString
    }
  | {
      type: 'bytes'
    }
  | {
      type: 'base64'
      base64: string
    }
  | {
      type: 'stream'
      stream: Stream
    }

/**
 * A class for working with images from a variety of sources.
 *
 * @see_also ImageContent
 *
 * This class is optimized for short-lived IO operations with multimodal LLMs.
 * By default all operations are performed in place. You can opt out of this behavior by passing `inPlace: false` to the methods.
 * Read operations are performed lazily, only when required, and at most once. Conversions between representations are performed only if necessary.
 *
 * Supported image formats:
 * - png
 * - jpeg
 * - webp
 * - gif
 * - bmp
 * - tiff
 *
 * Example usage:
 *
 * ```
 * const image = new Image(url)
 * const base64 = await image.base64() // "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA
 * ```
 * 
 * ```
 * const image = await new Image(url).setMaxSize(5).convert('png').base64()
 * ```
 *
 * **IMPORTANT**:
 * Base64 strings include the content type prefix `data:image/png;base64,` required by OpenAI-conformant APIs.
 * If you need to work with a base64 string that does not include the content type prefix, use the `splitBase64String` static method.
 *
 * Image references (like a URL, filepath, or stream) are dereferenced only when serializing to a base64 image string or a buffer.
 * Their contents are cached.
 * This means that the image is not loaded until the `base64` or `buffer` method is called.
 * Realized image values (like a buffer or base64 string) are referenced internally and converted to the desired representation on demand.
 * 
 * @param image The image source
 */
export class Image {
  private _source: Source
  private _format: ImageFormat | null = null
  private _buffer: Buffer | null = null
  private _modified: boolean = false
  private _sizeInBytes: number | null = null

  constructor(image: URLString | FilePath | Buffer | ArrayBuffer | Uint8Array | Uint8ClampedArray | Stream | URL) {
    if (image instanceof URL) {
      if (image.protocol === 'file:') {
        this._source = {
          type: 'file',
          path: path.resolve(image.pathname),
        }
      } else {
        this._source = {
          type: 'url',
          url: image.toString(),
        }
      }
    }
    if (typeof image === 'string') {
      if (image.startsWith('http://') || image.startsWith('https://')) {
        this._source = {
          type: 'url',
          url: image,
        }
        return
      } else if (image.startsWith('file://')) {
        const url = new URL(image)
        this._source = {
          type: 'file',
          path: path.resolve(url.pathname),
        }
        return
      } else if (image.startsWith('data:image/')) {
        const { base64, contentType } = Image.splitBase64String(image)
        this._source = {
          type: 'base64',
          base64: base64,
        }
        // @ts-ignore Let there be unknown image formats for now
        this._format = contentType as ImageFormat
        return
      } else {
        // Assume string references a local file
        this._source = {
          type: 'file',
          path: path.resolve(image),
        }
        return
      }
    }
    if (image instanceof Stream) {
      this._source = {
        type: 'stream',
        stream: image,
      }
      return
    }
    if (image instanceof Buffer) {
      this._source = {
        type: 'bytes',
      }
      this._buffer = image
      return
    }
    if (image instanceof Uint8Array || image instanceof Uint8ClampedArray || image instanceof ArrayBuffer) {
      this._source = {
        type: 'bytes',
      }
      this._buffer = Buffer.from(image)
      return
    }
    throw new Error('Invalid image source')
  }

  async stream(): Promise<Readable> {
    switch (this._source.type) {
      case 'file':
        return fs.createReadStream(this._source.path)
      case 'url':
        return fetch(this._source.url).then((response) => {
          const readableStream = response.body as WebReadableStream
          return Readable.fromWeb(readableStream)
        })
      case 'bytes':
        return Readable.from(this._buffer!)
      case 'base64':
        const buffer = Buffer.from(this._source.base64, 'base64')
        this._buffer = buffer
        return Readable.from(buffer)
      case 'stream':
        return this._source.stream as Readable
      default:
        throw new Error('Invalid image source')
    }
  }

  /**
   * Returns the base64 string of the image prefixed with the data URI scheme
   * @returns The base64 string of the image
   */
  async base64(): Promise<string> {
    if (this._buffer) {
      return this._buffer.toString('base64')
    }
    let base64: string
    switch (this._source.type) {
      case 'base64':
        if (!this._modified) {
          base64 = this._source.base64
        } else {
          // We always store a buffer when modified
          base64 = this._buffer!.toString('base64')
        }
        break
      case 'bytes':
        // Buffer is always set when received in the constructor
        // Uses the potentially in-place modified / resized / converted buffer
        //  when modifications made with inPlace: true
        base64 = this._buffer!.toString('base64')
        break
      case 'stream':
      case 'url':
      case 'file': {
        const stream = await this.stream()
        const chunks = []
        for await (const chunk of stream) {
          chunks.push(chunk)
        }
        // We expect this method is the last time we're called. We cache the buffer anyway
        // for sanity and expect to be dereferenced quickly
        this._buffer = Buffer.concat(chunks)
        base64 = this._buffer!.toString('base64')
        break
      }
    }

    const format = this._format || imageFormatFromBase64(base64)
    if (!format) {
      throw new Error('Unable to determine image format')
    }
    return `data:image/${format};base64,${base64}`
  }

  async buffer(): Promise<Buffer> {
    if (this._buffer || this._source.type === 'bytes') {
      // Returns the possibly modified buffer
      // or the original bytes (always set via constructor for source type bytes)
      return this._buffer!
    }

    let buffer: Buffer
    switch (this._source.type) {
      case 'base64':
        buffer = Buffer.from(this._source.base64, 'base64')
        break
      case 'stream':
      case 'url':
      case 'file': {
        // Must read the whole thing to get to a buffer
        const stream = await this.stream()
        const chunks = []
        for await (const chunk of stream) {
          chunks.push(chunk)
        }
        buffer = Buffer.concat(chunks)
        this._buffer = buffer
        break
      }
    }
    this._format = this._format || imageFormatFromBuffer(buffer)
    if (!this._format) {
      throw new Error('Unable to determine image format')
    }
    this._buffer = buffer
    return buffer
  }

  /**
   * Converts the image to a specified format using [sharp](https://sharp.pixelplumbing.com)
   * @param format The target format ('png', 'jpeg', 'webp', 'gif' )
   * @returns A new Image instance with the converted format
   */
  async convert(format: 'png' | 'jpeg' | 'webp' | 'gif', inPlace: boolean = true): Promise<Image> {
    if (format === this._format) {
      return this
    }
    const buffer = await this.buffer()
    // Reading to a buffer ensures _format is initialized for all source types
    if (format === this._format) {
      return this
    }

    const convertedBuffer = await sharp(buffer).toFormat(format).toBuffer()

    if (inPlace) {
      this._buffer = convertedBuffer
      this._format = format
      this._modified = true
      return this
    } else {
      return new Image(convertedBuffer)
    }
  }

  /**
   * Resizes an image to a maximum size in MB
   * @param buffer The image buffer
   * @param maxSizeMB The maximum size in MB
   * @returns The resized image buffer
   */
  async setMaxSize(maxSizeMB: number, inPlace: boolean = true): Promise<Image> {
    const buffer = this._buffer || (await this.buffer())

    // Early exit if the image is already less than or equal to the max size
    const currentSizeMB = buffer.length / (1024 * 1024)
    if (currentSizeMB <= maxSizeMB) {
      return this
    }

    const image = sharp(buffer)
    const metadata = await image.metadata()

    if (!metadata.width || !metadata.height) {
      throw new Error('Unable to get image dimensions')
    }

    const aspectRatio = metadata.width / metadata.height
    let newWidth = metadata.width
    let newHeight = metadata.height

    // Calculate target size in bytes
    const targetSizeBytes = maxSizeMB * 1024 * 1024

    while ((newWidth * newHeight * (metadata.channels || 3)) / 8 > targetSizeBytes) {
      newWidth = Math.floor(newWidth * 0.9)
      newHeight = Math.floor(newWidth / aspectRatio)
    }

    const resizedBuffer = await image
      .resize(newWidth, newHeight, { fit: 'inside', withoutEnlargement: true })
      .toBuffer()

    if (inPlace) {
      this._buffer = resizedBuffer
      this._modified = true
      return this
    } else {
      return new Image(resizedBuffer)
    }
  }

  /**
   * Splits a base64 string into its content type and base64 data
   * Required for some non-OpenAI-compliant APIs
   * @param base64String The base64 string
   * @returns The content type and base64 data
   */
  static splitBase64String(base64String: string): { contentType: string; base64: string } {
    const contentType = base64String.split(';')[0]
    const base64 = base64String.split(',')[1]
    return { contentType, base64 }
  }
}
