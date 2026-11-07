// The hero's circuit: a Glider ISA program compiled and run by destbreso.com's own Game of Life engine, one period of it
// written out as every generation's live cells (circuit.json). Run from a checkout of the site's repository, whose
// engine it imports:
//   npx tsx <this repository>/tools/hero/frames.ts <this repository>/tools/hero/circuit.json
import { writeFileSync } from "node:fs";
import { resolve } from "node:path";

const SOURCE = "a = EMIT gosper SE AT 0 0\nb = REFLECT a AT 34 LEFT\nABSORB b AT 34";
const PERIOD = 30; // the Gosper gun's, so the last frame leads back into the first
const WARMUP = 900; // generations for the streams to fill the board before the period is read
const MARGIN = 4;

async function main() {
  const out = process.argv[2];
  const site = resolve(process.cwd(), "lib/games/game-of-life");
  const { LifeSession } = await import(`${site}/session`);
  const { collisions } = await import(`${site}/circuits/crossings`);
  const { compileProgram, parseProgram } = await import(`${site}/circuits/program`);
  const { extent } = await import(`${site}/circuits/geometry`);

  const compiled = compileProgram(parseProgram(SOURCE));
  if (collisions(compiled).length) throw new Error("the circuit's streams run into something");
  const [x0, y0, x1, y1] = extent(compiled.pieces.flatMap((p: { cells: number[][] }) => p.cells));
  const box: [number, number, number, number] = [x0 - MARGIN, y0 - MARGIN, x1 + MARGIN, y1 + MARGIN];
  const s = new LifeSession();
  s.place(SOURCE, { x: 0, y: 0 }, "hero");
  for (let i = 0; i < WARMUP; i++) s.step();
  const frames: number[][][] = [];
  for (let i = 0; i < PERIOD; i++) {
    frames.push(s.cellsIn(...box).map(([x, y]: number[]) => [x, y]));
    s.step();
  }
  const key = (f: number[][]) => f.map((q) => q.join(",")).sort().join(";");
  if (key(s.cellsIn(...box).map(([x, y]: number[]) => [x, y])) !== key(frames[0])) throw new Error("the period does not close");
  writeFileSync(out, JSON.stringify({ source: SOURCE, period: PERIOD, box, frames }));
  console.log("wrote", out, frames.length, "frames");
}

main();
