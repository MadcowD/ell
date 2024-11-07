import {  test } from "mocha"
import { imageFormatFromBase64 } from "../src/util/image"
import assert from 'assert'


test('detectImageFormatFromBase64', () => {
  // Test empty string
  assert.equal(imageFormatFromBase64(''), null)

  // Test JPEG
  assert.equal(imageFormatFromBase64('/9j/4AAQSkZJRgABAQEAYABgAAD'), 'jpeg')

  // Test PNG
  assert.equal(imageFormatFromBase64('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=='), 'png')

  // Test GIF
  assert.equal(imageFormatFromBase64('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'), 'gif')

  // Test BMP
  assert.equal(imageFormatFromBase64('Qk0eAAAAAAAAABoAAAAMAAAAAQABAAEAGAAAAP8A'), 'bmp')

  // Test TIFF (little-endian)
  assert.equal(imageFormatFromBase64('SUkqAA'), 'tiff')

  // Test TIFF (big-endian)
  assert.equal(imageFormatFromBase64('TU0AKg'), 'tiff')

  // Test WebP
  assert.equal(imageFormatFromBase64('UklGRh4AAABXRUJQVlA4'), 'webp')

  // Test unknown format
  assert.equal(imageFormatFromBase64('SGVsbG8gV29ybGQh'), null)
})
