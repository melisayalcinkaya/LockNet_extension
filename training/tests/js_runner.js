// Python testlerinin JS tarafını çalıştırdığı yardımcı.
// stdin: {"gorev": "...", "metinler": [...]}  stdout: JSON sonuç listesi
const fs = require("fs");
const path = require("path");
const lib = path.resolve(__dirname, "../../extension/lib");
const { onIsle } = require(path.join(lib, "preprocess.js"));
const { ngramlar, murmur3 } = require(path.join(lib, "features.js"));
const { modelOlustur } = require(path.join(lib, "model.js"));

const girdi = JSON.parse(fs.readFileSync(0, "utf8"));
let cikti;
if (girdi.gorev === "on_isle") cikti = girdi.metinler.map(onIsle);
else if (girdi.gorev === "hash") cikti = girdi.metinler.map((m) => ngramlar(m).map(murmur3));
else if (girdi.gorev === "skor") {
  const dizin = path.resolve(__dirname, "../..", girdi.model_dizini);
  const meta = JSON.parse(fs.readFileSync(path.join(dizin, "meta.json"), "utf8"));
  const b = fs.readFileSync(path.join(dizin, "weights.bin"));
  const model = modelOlustur(meta, b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength));
  cikti = girdi.metinler.map(model.skor);
}
process.stdout.write(JSON.stringify(cikti));
