module.exports = {
  apps: [
    {
      name: 'gold-bot',
      script: './venv/bin/python3',
      args: './gold_bot.py',
      cwd: '/root/ctrader-g4trade-bot',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1'
      },
      error_file: '/root/ctrader-g4trade-bot/logs/bot-error.log',
      out_file: '/root/ctrader-g4trade-bot/logs/bot-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true
    },
    {
      name: 'g4trade-dashboard',
      script: './venv/bin/python3',
      args: './dashboard/app.py',
      cwd: '/root/ctrader-g4trade-bot',
      interpreter: 'none',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1'
      },
      error_file: '/root/ctrader-g4trade-bot/logs/dashboard-error.log',
      out_file: '/root/ctrader-g4trade-bot/logs/dashboard-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true
    }
  ]
};
