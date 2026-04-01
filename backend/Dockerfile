# ==========================================
# 后端 Dockerfile (Node.js + NestJS)
# ==========================================

FROM node:20-alpine AS base

# 安装必要依赖
RUN apk add --no-cache dumb-init

# 设置工作目录
WORKDIR /app

# 阶段1: 依赖安装
FROM base AS deps

# 复制依赖文件
COPY package.json package-lock.json* ./

# 安装生产依赖
RUN npm ci --only=production && npm cache clean --force

# 阶段2: 构建
FROM base AS builder

# 复制依赖
COPY --from=deps /app/node_modules ./node_modules

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 阶段3: 生产运行
FROM base AS runner

# 创建非root用户
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nestjs -u 1001

# 设置环境变量
ENV NODE_ENV=production
ENV PORT=3000

# 复制生产依赖
COPY --from=deps --chown=nestjs:nodejs /app/node_modules ./node_modules

# 复制构建产物
COPY --from=builder --chown=nestjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nestjs:nodejs /app/package.json ./

# 切换到非root用户
USER nestjs

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/health', (r) => r.statusCode === 200 ? process.exit(0) : process.exit(1))"

# 使用dumb-init处理信号
ENTRYPOINT ["dumb-init", "--"]

# 启动应用
CMD ["node", "dist/main.js"]
