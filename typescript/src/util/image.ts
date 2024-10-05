import * as path from 'path'
import * as fs from 'fs'
import { Readable, Stream } from 'stream'
import { ReadableStream as WebReadableStream } from 'stream/web'

type URLString = string
type FilePath = string

export function detectImageFormatFromBase64(base64String: string): string {
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

export function detectImageFormatFromBuffer(buffer: Buffer): string {
  return detectImageFormatFromBase64(buffer.subarray(0, 16).toString('base64'))
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
export class Image {
  private _source: Source
  private _format: 'png' | 'jpeg' | 'webp' | 'gif' | 'bmp' | 'tiff' | 'unknown'

  constructor(image: URLString | FilePath | URL | Buffer | ArrayBuffer | Uint8Array | Uint8ClampedArray | Stream) {
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
        return
      }
    }
    if (image instanceof Buffer) {
      this._source = {
        type: 'bytes',
        buffer: image,
      }
      return
    }
    if (image instanceof ArrayBuffer) {
      this._source = {
        type: 'bytes',
        buffer: Buffer.from(image),
      }
      return
    }
    if (image instanceof Uint8Array) {
      this._source = {
        type: 'bytes',
        buffer: Buffer.from(image),
      }
      return
    }
    if (image instanceof Uint8ClampedArray) {
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
      default:
        throw new Error('Invalid image source')
    }
  }
  async base64(): Promise<string> {
    const stream = await this.stream()
    const chunks = []
    for await (const chunk of stream) {
      chunks.push(chunk)
    }
    return Buffer.concat(chunks).toString('base64')
  }
}

// const img = new Image(
//   'https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.reddit.com%2Fr%2Fcats%2Fcomments%2Fldtzkv%2Fhere_is_a_random_cat_pic_no_one_asked_for%2F&psig=AOvVaw25es7bFSVNbutMd6YDDfCV&ust=1728251451806000&source=images&cd=vfe&opi=89978449&ved=0CBEQjRxqFwoTCPCY8cCc-IgDFQAAAAAdAAAAABAE'
// )

// img.base64().then(console.log)
