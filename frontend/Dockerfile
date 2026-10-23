# ===================================================
# Giai đoạn 1: Build ứng dụng ReactJS (Node.js)
# ===================================================
FROM node:18-alpine AS build
WORKDIR /app

# Cài đặt dependencies
COPY package*.json ./
RUN npm install

# Sao chép mã nguồn và đóng gói bản production
COPY . .
RUN npm run build

# ===================================================
# Giai đoạn 2: Phục vụ ứng dụng qua Nginx Production
# ===================================================
FROM nginx:alpine

# Sao chép thư mục build từ giai đoạn 1 sang Nginx root
COPY --from=build /app/build /usr/share/nginx/html

# Sao chép cấu hình Nginx reverse proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Mở cổng HTTP 80
EXPOSE 80

# Chạy Nginx
CMD ["nginx", "-g", "daemon off;"]

