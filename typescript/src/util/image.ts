import * as path from 'path'
import * as fs from 'fs'
import { Readable, Stream } from 'stream'
import { ReadableStream as WebReadableStream } from 'stream/web'

type URLString = string
type FilePath = string

type ImageFormat = 'png' | 'jpeg' | 'webp' | 'gif' | 'bmp' | 'tiff' | 'unknown'

export function imageFormatFromBase64(base64String: string): ImageFormat {
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
    return 'unknown'
  }
}

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
      buffer: Buffer
    }
  | {
      type: 'base64'
      base64: string
    }
  | {
      type: 'stream'
      stream: Stream
    }

export class Image {
  private _source: Source
  private _format: ImageFormat | null = null

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
      if (image.startsWith('http')) {
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
        this._source = {
          type: 'base64',
          base64: image.split(',')[1],
        }
        this._format = image.split(';')[0].split('/')[1] as 'png' | 'jpeg' | 'webp' | 'gif' | 'bmp' | 'tiff'
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
        buffer: image,
      }
      return
    }
    if (image instanceof Uint8Array || image instanceof Uint8ClampedArray || image instanceof ArrayBuffer) {
      this._source = {
        type: 'bytes',
        buffer: Buffer.from(image),
      }
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
        return Readable.from(Buffer.from(this._source.buffer))
      case 'base64':
        return Readable.from(Buffer.from(this._source.base64, 'base64'))
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
    let base64: string
    switch (this._source.type) {
      case 'base64':
        base64 = this._source.base64
        break
      case 'bytes':
        base64 = Buffer.from(this._source.buffer).toString('base64')
        break
      case 'stream':
      case 'url':
      case 'file': {
        const stream = await this.stream()
        const chunks = []
        for await (const chunk of stream) {
          chunks.push(chunk)
        }
        base64 = Buffer.concat(chunks).toString('base64')
        break
      }
    }

    const format = this._format || imageFormatFromBase64(base64)
    return `data:image/${format};base64,${base64}`
  }

  async buffer(): Promise<Buffer> {
    let buffer: Buffer
    switch (this._source.type) {
      case 'bytes':
        buffer = this._source.buffer
        break
      case 'base64':
        buffer = Buffer.from(this._source.base64, 'base64')
        break
      case 'stream':
      case 'url':
      case 'file': {
        const stream = await this.stream()
        const chunks = []
        for await (const chunk of stream) {
          chunks.push(chunk)
        }
        buffer = Buffer.concat(chunks)
        break
      }
    }
    this._format = this._format || imageFormatFromBuffer(buffer)
    return buffer
  }
}

// const img = new Image('https://i.redd.it/zwfggeplutf61.jpg')
// const img = new Image('../___scratch_space___/cat.jpg')
// const img = new Image('/Users/alexdixon/projects/ell/___scratch_space___/cat.jpg')
//
// img.base64().then(console.log)
