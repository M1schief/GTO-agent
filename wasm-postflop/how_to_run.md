# 运行 [Wasm-postflop](https://github.com/b-inary/wasm-postflop) 步骤

## 1. Clone Project

git clone https://github.com/b-inary/wasm-postflop.git

## 2. Install nodejs

 [Downloads node.js](https://nodejs.org/en/download) 推荐windows用prebuilt installer,我用的版本20.18.4，安装完后加一下环境变量PATH

```
node -v
```

确认一下安装正确

## 3. Prerequisites

```bash
rustup install nightly
rustup +nightly component add rust-src
rustup target add wasm32-unknown-unknown
cargo install wasm-pack
npm install
```

## 4. Build

run wasm之前需要改一下代码\pkg\solver-mt\snippets\solver-9ec3a3d9d4184257\workerHelpers.js的56行改成这个

```js
const pkg = await import("../../solver.js");
```

```bash
npm run wasm
npm run build
```

## 5. Serve

```bash
npm run serve
```
