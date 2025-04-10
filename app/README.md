# XCA-Bot Dashboard

A modern web interface for the XCA-Bot cryptocurrency address monitoring system.

## Features

- 📊 **Dashboard Interface**: User-friendly dashboard to control the monitoring service
- 💰 **Contract Address Viewing**: See detected contract addresses from Twitter/X
- 📈 **Ticker Symbol Tracking**: Monitor cryptocurrency ticker symbols (e.g., $BTC, $ETH)
- ⚙️ **Configuration Management**: Configure Twitter API keys and Telegram destinations
- 👤 **Username Management**: Add/remove Twitter/X usernames to monitor
- 🚀 **Real-time Status**: View real-time monitoring status and statistics

## Getting Started

### Prerequisites

- Node.js 14.x or later
- XCA-Bot backend running on localhost:8000 (or configured API URL)

### Installation

1. Install dependencies:

```bash
npm install
```

2. Run the development server:

```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Configuration

The dashboard connects to the XCA-Bot API server. By default, it connects to `http://localhost:8000/api/v1`.

To change the API URL, set the `NEXT_PUBLIC_API_BASE_URL` environment variable or modify the API configuration in `lib/api.js`.

## Building for Production

Build the application for production:

```bash
npm run build
```

Start the production server:

```bash
npm start
```

### Production Deployment Options

For production deployment, consider these options:

1. **Standalone Mode**:
   ```bash
   npm run build
   npm start
   ```

2. **Using a Process Manager** (e.g., PM2):
   ```bash
   npm install -g pm2
   pm2 start npm --name "xca-dashboard" -- start
   ```

3. **Docker Deployment**:
   ```
   # Example Dockerfile is available in the repository
   docker build -t xca-dashboard .
   docker run -p 3000:3000 xca-dashboard
   ```

## Error Handling

The dashboard includes robust error handling for API communication issues:

- Connection timeouts (5-second limit)
- Detailed error messages for common failures
- Automatic retry mechanisms
- User-friendly error displays

If the backend API is unavailable, the dashboard will display clear error messages with troubleshooting steps.

## Project Structure

- `pages/`: Next.js pages
- `components/`: React components
- `lib/`: Utility functions and API integration
- `styles/`: CSS styles
- `public/`: Static assets

## API Integration

The dashboard integrates with the XCA-Bot backend API using the following endpoints:

- Status information: `/status`
- Monitoring control: `/monitoring/start`, `/monitoring/stop`, `/monitoring/check-now`
- Match retrieval: `/matches`
- Configuration management: `/config`
- Telegram settings: `/telegram/destinations/*`

## Troubleshooting

- **API Connection Issues**: Verify the backend is running and the API URL is correct
- **"Failed to fetch" Errors**: Check if the backend server is accessible
- **Slow Loading**: The dashboard implements timeouts to prevent indefinite loading states
- **Configuration Errors**: Ensure your backend is properly configured with valid API keys

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Deployment Options

### Option 1: Vercel (Recommended)

The easiest way to deploy this Next.js application is with [Vercel](https://vercel.com), the platform built by the creators of Next.js.

1. Create a Vercel account at https://vercel.com/signup
2. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```
3. From your project directory, run:
   ```bash
   vercel
   ```
4. Follow the prompts to deploy your application
5. Set environment variables in the Vercel dashboard:
   - `NEXT_PUBLIC_API_BASE_URL`: URL to your backend API

### Option 2: Netlify

1. Create a Netlify account at https://netlify.com
2. Install the Netlify CLI:
   ```bash
   npm install -g netlify-cli
   ```
3. From your project directory, run:
   ```bash
   netlify deploy
   ```
4. Follow the prompts to deploy your application
5. Set environment variables in the Netlify dashboard

### Option 3: Docker

You can containerize the application for deployment:

1. Create a `Dockerfile` in the root of your project:
   ```dockerfile
   FROM node:20-alpine as builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci
   COPY . .
   RUN npm run build

   FROM node:20-alpine as runner
   WORKDIR /app
   ENV NODE_ENV production
   COPY --from=builder /app/public ./public
   COPY --from=builder /app/.next ./.next
   COPY --from=builder /app/node_modules ./node_modules
   COPY --from=builder /app/package.json ./package.json

   EXPOSE 3000
   CMD ["npm", "start"]
   ```

2. Build the Docker image:
   ```bash
   docker build -t xca-bot-dashboard .
   ```

3. Run the container:
   ```bash
   docker run -p 3000:3000 -e NEXT_PUBLIC_API_BASE_URL=http://your-api-url xca-bot-dashboard
   ```

### Option 4: Static Export

For simple hosting solutions:

1. Add the following to your `next.config.js`:
   ```js
   const nextConfig = {
     output: 'export',
     // ... other config
   };
   ```

2. Build the static version:
   ```bash
   npm run build
   ```

3. The static site will be in the `out` directory, which you can deploy to any static hosting service like GitHub Pages, Netlify, or Amazon S3.

## Environment Variables

Set these environment variables for production:

- `NEXT_PUBLIC_API_BASE_URL`: URL to your backend API (default: http://localhost:8000/api/v1)

## Backend Integration

For the dashboard to function properly, you need to have the XCA-Bot backend running and accessible to your frontend application. Make sure the API URL is correctly configured through the environment variables. 