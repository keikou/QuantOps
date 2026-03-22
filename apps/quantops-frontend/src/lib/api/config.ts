export const API_BASE_URL = (process.env.QUANTOPS_API_BASE_URL || 'http://127.0.0.1:8010').trim().replace(/\/+$/, '');
export const API_TIMEOUT_MS = Number(process.env.QUANTOPS_API_TIMEOUT_MS || 8000);
export const USE_PROXY = process.env.QUANTOPS_USE_PROXY !== 'false';
export const ENABLE_MOCK_FALLBACK = process.env.QUANTOPS_ENABLE_MOCK_FALLBACK === 'true';
export const ENABLE_PROXY_MOCK = process.env.QUANTOPS_ENABLE_PROXY_MOCK === 'true';
export const API_DEBUG_ERRORS = process.env.NEXT_PUBLIC_QUANTOPS_API_DEBUG_ERRORS !== 'false';
