import {  test } from "mocha"
import { detectImageFormatFromBase64 } from "../src/util/image"
import assert from 'assert'


test('detectImageFormatFromBase64', () => {
  // Test empty string
  assert.equal(detectImageFormatFromBase64(''), 'unknown')

  // Test JPEG
  assert.equal(detectImageFormatFromBase64('/9j/4AAQSkZJRgABAQEAYABgAAD'), 'jpeg')

  // Test PNG
  assert.equal(detectImageFormatFromBase64('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=='), 'png')

  // Test GIF
  assert.equal(detectImageFormatFromBase64('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'), 'gif')

  // Test BMP
  assert.equal(detectImageFormatFromBase64('Qk0eAAAAAAAAABoAAAAMAAAAAQABAAEAGAAAAP8A'), 'bmp')

  // Test TIFF (little-endian)
  assert.equal(detectImageFormatFromBase64('SUkqAA'), 'tiff')

  // Test TIFF (big-endian)
  assert.equal(detectImageFormatFromBase64('TU0AKg'), 'tiff')

  // Test WebP
  assert.equal(detectImageFormatFromBase64('UklGRh4AAABXRUJQVlA4'), 'webp')

  // Test unknown format
  assert.equal(detectImageFormatFromBase64('SGVsbG8gV29ybGQh'), 'unknown')
})
