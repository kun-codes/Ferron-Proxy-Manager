FROM node:25-alpine AS builder

WORKDIR /app

RUN npm install -g pnpm

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm run build

FROM node:25-alpine

WORKDIR /app

COPY --from=builder /app/build ./build

EXPOSE 3000

CMD ["node", "build"]
