#!/usr/bin/env node

/**
 * Finds empty documents in a data.json file.
 *
 * Usage: './scripts/empty data.json
 * Example: './scripts/empty data.json
 */
const fs = require('fs')
const ndjson = require('ndjson')

const args = process.argv.slice(2)
const filepath = args[0]
const toHave = args[1] || 'descripcion'
const toPrint = args[2] || 'id_compranet'

function run () {
  fs.createReadStream(filepath)
    .pipe(ndjson.parse())
    .on('data', function (obj) {
      if (!obj[toHave]) {
        console.log(obj[toPrint])
      }
    })
}

run()
