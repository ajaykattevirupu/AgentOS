# Use Node 20 (required by Next.js)
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (package-lock.json optional)
COPY package*.json ./
RUN npm install

# Copy all project files
COPY . .

# Expose frontend port
EXPOSE 3000

# Start Next.js dev server
CMD ["npm", "run", "dev"]
