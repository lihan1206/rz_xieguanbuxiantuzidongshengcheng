# ==========================================
# 前端 Dockerfile
# 多阶段构建优化镜像大小
# ==========================================

# 阶段1: 依赖安装
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat

WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json* ./

# 安装依赖
RUN npm ci --only=production

# 阶段2: 构建
FROM node:20-alpine AS builder

WORKDIR /app

# 从deps阶段复制node_modules
COPY --from=deps /app/node_modules ./node_modules

# 复制源代码
COPY . .

# 构建参数
ARG VITE_API_BASE_URL
ARG VITE_WS_URL
ARG VITE_APP_VERSION

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_WS_URL=${VITE_WS_URL}
ENV VITE_APP_VERSION=${VITE_APP_VERSION}

# 构建应用
RUN npm run build

# 阶段3: 生产运行
FROM nginx:alpine AS runner

# 安装安全更新
RUN apk update && apk upgrade && apk add --no-cache curl

# 复制自定义nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 从builder阶段复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 创建非root用户
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 && \
    chown -R nextjs:nodejs /usr/share/nginx/html

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
