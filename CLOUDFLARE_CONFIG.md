# Cloudflare Configuration for Website Status Monitor

This guide helps you configure Cloudflare optimally for your Website Status Monitor to ensure real-time data while maximizing performance.

## 🚀 Quick Setup

### 1. Page Rules (Recommended)

Set up these Page Rules in your Cloudflare dashboard:

#### API Endpoints - No Cache
- **URL Pattern**: `yourdomain.com/api/*`
- **Settings**:
  - Cache Level: Bypass
  - Edge Cache TTL: 1 second
  - Browser Cache TTL: 1 second

#### Static Assets - Long Cache
- **URL Pattern**: `yourdomain.com/*.js` or `yourdomain.com/*.css`
- **Settings**:
  - Cache Level: Standard
  - Edge Cache TTL: 1 hour
  - Browser Cache TTL: 1 day

#### HTML Pages - Short Cache
- **URL Pattern**: `yourdomain.com/`
- **Settings**:
  - Cache Level: Standard
  - Edge Cache TTL: 30 seconds
  - Browser Cache TTL: 1 minute

### 2. Cache Rules (Cloudflare Pro+)

If you have Cloudflare Pro or higher, use Cache Rules instead:

```
# Rule 1: Bypass API Cache
Expression: (http.request.uri.path contains "/api/")
Action: Bypass cache

# Rule 2: Cache Static Assets
Expression: (http.request.uri.path ends with ".js") or (http.request.uri.path ends with ".css")
Action: Cache
Edge TTL: 1 hour
Browser TTL: 1 day

# Rule 3: Short Cache for HTML
Expression: (http.request.uri.path eq "/" or http.request.uri.path ends with ".html")
Action: Cache
Edge TTL: 30 seconds
Browser TTL: 60 seconds
```

## 🔧 Advanced Configuration

### Worker Script (Optional)

For maximum control, you can use a Cloudflare Worker:

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  
  // Bypass cache for API endpoints
  if (url.pathname.startsWith('/api/')) {
    const response = await fetch(request, {
      cf: {
        cacheTtl: 0,
        cacheEverything: false
      }
    })
    
    // Add no-cache headers
    const headers = new Headers(response.headers)
    headers.set('Cache-Control', 'no-cache, no-store, must-revalidate')
    headers.set('CF-Cache-Status', 'BYPASS')
    
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: headers
    })
  }
  
  // Default behavior for other requests
  return fetch(request)
}
```

### Custom Headers

Add these custom headers in Cloudflare Transform Rules:

```
# For API requests
If: starts_with(http.request.uri.path, "/api/")
Then: Set response header "X-Cache-Status" to "BYPASS"

# For static assets
If: ends_with(http.request.uri.path, ".js") or ends_with(http.request.uri.path, ".css")
Then: Set response header "X-Cache-Status" to "CACHED"
```

## 🧪 Testing Your Configuration

### 1. Check Cache Status

Open browser developer tools and look for these headers in API responses:
- `CF-Cache-Status: BYPASS` ✅ (Good - no caching)
- `CF-Cache-Status: HIT` ❌ (Bad - cached data)
- `CF-Cache-Status: MISS` ✅ (Good - fresh data)

### 2. Monitor Data Freshness

The status monitor shows cache information at the bottom:
- CF Cache: BYPASS ✅
- Data age: <60s ✅
- Click "Force Refresh" to test cache bypass

### 3. Performance Testing

```bash
# Test API endpoint caching
curl -I https://yourdomain.com/api/status

# Should show:
# CF-Cache-Status: BYPASS
# Cache-Control: no-cache, no-store, must-revalidate
```

## 🛠️ Troubleshooting

### Issue: Stale Data
**Symptoms**: Status not updating, old timestamps
**Solutions**:
1. Check Page Rules are correctly configured
2. Use "Force Refresh" in the web UI
3. Purge cache manually in Cloudflare dashboard

### Issue: Slow Loading
**Symptoms**: Long load times, poor performance
**Solutions**:
1. Ensure static assets are being cached
2. Enable Cloudflare compression (Brotli/Gzip)
3. Use Cloudflare's rocket loader for JS optimization

### Issue: Mixed Cache Status
**Symptoms**: Some requests cached, others not
**Solutions**:
1. Check Page Rule order (they execute top to bottom)
2. Use more specific URL patterns
3. Consider using Cache Rules instead

## 📊 Optimal Settings Summary

| Content Type | Edge Cache | Browser Cache | CF Settings |
|-------------|------------|---------------|-------------|
| API Endpoints | Bypass | No cache | Cache Level: Bypass |
| Static Assets | 1 hour | 1 day | Cache Level: Standard |
| HTML Pages | 30 seconds | 1 minute | Cache Level: Standard |

## 🔍 Monitoring

Enable these Cloudflare features for better monitoring:
- **Analytics**: Track cache hit rates
- **Logs**: Monitor API request patterns  
- **Security**: Enable bot protection for API endpoints
- **Performance**: Use APO (Automatic Platform Optimization) for static content

## 💡 Pro Tips

1. **Test First**: Always test configuration changes in a staging environment
2. **Monitor Cache Hit Rates**: Aim for >80% cache hit rate on static assets
3. **Use Custom Domains**: Avoid caching issues with custom API subdomains
4. **Enable HTTP/3**: For better performance on modern browsers
5. **Set Up Alerts**: Monitor your origin server for increased load

---

For more help, check the [Cloudflare Documentation](https://developers.cloudflare.com/) or contact support. 