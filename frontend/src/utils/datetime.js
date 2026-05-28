export function parseServerTimestamp(timestamp) {
  if (!timestamp) {
    return null;
  }

  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(timestamp);
  const parsed = new Date(hasTimezone ? timestamp : `${timestamp}Z`);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatServerTime(timestamp, options = {}) {
  const parsed = parseServerTimestamp(timestamp);
  if (!parsed) {
    return "Invalid time";
  }
  return parsed.toLocaleTimeString([], options);
}

export function formatServerDateTime(timestamp, options = {}) {
  const parsed = parseServerTimestamp(timestamp);
  if (!parsed) {
    return "Invalid time";
  }
  return parsed.toLocaleString([], options);
}
