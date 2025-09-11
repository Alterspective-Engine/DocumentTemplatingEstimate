/**
 * Security middleware for Express server
 * Adds comprehensive security headers to all responses
 */

function securityHeaders() {
  return (req, res, next) => {
    // Content Security Policy - Prevent XSS attacks
    res.setHeader(
      'Content-Security-Policy',
      "default-src 'self'; " +
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; " +
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; " +
      "font-src 'self' https://fonts.gstatic.com data:; " +
      "img-src 'self' data: https: blob:; " +
      "connect-src 'self' ws: wss: http://localhost:* https://api.github.com; " +
      "frame-ancestors 'none'; " +
      "base-uri 'self'; " +
      "form-action 'self';"
    );
    
    // Prevent clickjacking
    res.setHeader('X-Frame-Options', 'DENY');
    
    // Prevent MIME type sniffing
    res.setHeader('X-Content-Type-Options', 'nosniff');
    
    // Enable XSS filter in older browsers
    res.setHeader('X-XSS-Protection', '1; mode=block');
    
    // Referrer Policy
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    
    // Permissions Policy (formerly Feature Policy)
    res.setHeader(
      'Permissions-Policy',
      'camera=(), microphone=(), geolocation=(), payment=()'
    );
    
    // Strict Transport Security (HSTS) - only in production
    if (process.env.NODE_ENV === 'production') {
      res.setHeader(
        'Strict-Transport-Security',
        'max-age=31536000; includeSubDomains; preload'
      );
    }
    
    // Remove powered by header
    res.removeHeader('X-Powered-By');
    
    next();
  };
}

module.exports = { securityHeaders };