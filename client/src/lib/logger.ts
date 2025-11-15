type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: any;
  stack?: string;
  userAgent?: string;
  url?: string;
}

class Logger {
  private logs: LogEntry[] = [];
  private maxLogs = 1000;
  private isDevelopment = import.meta.env.DEV;

  private createEntry(level: LogLevel, message: string, data?: any): LogEntry {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data,
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    if (data instanceof Error) {
      entry.stack = data.stack;
    }

    return entry;
  }

  private persistLog(entry: LogEntry) {
    this.logs.push(entry);
    
    // Keep only recent logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Store in localStorage for persistence
    try {
      const storedLogs = JSON.parse(localStorage.getItem('app_logs') || '[]');
      storedLogs.push(entry);
      localStorage.setItem('app_logs', JSON.stringify(storedLogs.slice(-100)));
    } catch (e) {
      console.error('Failed to persist log:', e);
    }

    // Send critical errors to backend
    if (entry.level === 'error') {
      this.sendToBackend(entry);
    }
  }

  private async sendToBackend(entry: LogEntry) {
    try {
      await fetch('/api/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry),
      });
    } catch (e) {
      console.error('Failed to send log to backend:', e);
    }
  }

  debug(message: string, data?: any) {
    if (this.isDevelopment) {
      console.debug(`[DEBUG] ${message}`, data);
      this.persistLog(this.createEntry('debug', message, data));
    }
  }

  info(message: string, data?: any) {
    console.info(`[INFO] ${message}`, data);
    this.persistLog(this.createEntry('info', message, data));
  }

  warn(message: string, data?: any) {
    console.warn(`[WARN] ${message}`, data);
    this.persistLog(this.createEntry('warn', message, data));
  }

  error(message: string, data?: any) {
    console.error(`[ERROR] ${message}`, data);
    this.persistLog(this.createEntry('error', message, data));
  }

  getLogs(level?: LogLevel): LogEntry[] {
    return level ? this.logs.filter(log => log.level === level) : this.logs;
  }

  clearLogs() {
    this.logs = [];
    localStorage.removeItem('app_logs');
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }
}

export default new Logger();
