FROM node:22-alpine AS base

WORKDIR /app

COPY apps/web/package.json ./apps/web/
WORKDIR /app/apps/web
RUN npm install

COPY apps/web ./
RUN npm run build

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "run", "start"]

