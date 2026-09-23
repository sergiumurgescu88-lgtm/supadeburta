module.exports = {
  apps: [
    // ============ ALPHA (Sniper - Breakout M15/H1) ============
    {
      name: "alpha-sniper-engine",
      script: "/root/trinity-fund/alpha-sniper/strategy_engine_sniper.py",
      interpreter: "/root/trinity-fund/alpha-sniper/venv/bin/python3",
      cwd: "/root/trinity-fund/alpha-sniper",
      log_file: "/var/log/trinity/alpha-engine.log",
      out_file: "/var/log/trinity/alpha-engine-out.log",
      error_file: "/var/log/trinity/alpha-engine-error.log",
      restart_delay: 5000
    },
    {
      name: "alpha-gold-bot",
      script: "/root/trinity-fund/alpha-sniper/gold_bot.py",
      interpreter: "/root/trinity-fund/alpha-sniper/venv/bin/python3",
      cwd: "/root/trinity-fund/alpha-sniper",
      log_file: "/var/log/trinity/alpha-bot.log",
      out_file: "/var/log/trinity/alpha-bot-out.log",
      error_file: "/var/log/trinity/alpha-bot-error.log",
      restart_delay: 5000
    },
    {
      name: "alpha-dashboard",
      script: "/root/trinity-fund/alpha-sniper/dashboard/app.py",
      interpreter: "/root/trinity-fund/alpha-sniper/venv/bin/python3",
      cwd: "/root/trinity-fund/alpha-sniper",
      log_file: "/var/log/trinity/alpha-dashboard.log",
      out_file: "/var/log/trinity/alpha-dashboard-out.log",
      error_file: "/var/log/trinity/alpha-dashboard-error.log",
      restart_delay: 5000
    },
    // ============ BETA (Trend Follower - H4/D1) ============
    {
      name: "beta-trend-engine",
      script: "/root/trinity-fund/beta-trend/strategy_engine_trend.py",
      interpreter: "/root/trinity-fund/beta-trend/venv/bin/python3",
      cwd: "/root/trinity-fund/beta-trend",
      log_file: "/var/log/trinity/beta-engine.log",
      out_file: "/var/log/trinity/beta-engine-out.log",
      error_file: "/var/log/trinity/beta-engine-error.log",
      restart_delay: 5000
    },
    {
      name: "beta-gold-bot",
      script: "/root/trinity-fund/beta-trend/gold_bot.py",
      interpreter: "/root/trinity-fund/beta-trend/venv/bin/python3",
      cwd: "/root/trinity-fund/beta-trend",
      log_file: "/var/log/trinity/beta-bot.log",
      out_file: "/var/log/trinity/beta-bot-out.log",
      error_file: "/var/log/trinity/beta-bot-error.log",
      restart_delay: 5000
    },
    {
      name: "beta-dashboard",
      script: "/root/trinity-fund/beta-trend/dashboard/app.py",
      interpreter: "/root/trinity-fund/beta-trend/venv/bin/python3",
      cwd: "/root/trinity-fund/beta-trend",
      log_file: "/var/log/trinity/beta-dashboard.log",
      out_file: "/var/log/trinity/beta-dashboard-out.log",
      error_file: "/var/log/trinity/beta-dashboard-error.log",
      restart_delay: 5000
    },
    // ============ GAMMA (Scalper - Mean Reversion M1/M5) ============
    {
      name: "gamma-scalp-engine",
      script: "/root/trinity-fund/gamma-scalp/strategy_engine_scalp.py",
      interpreter: "/root/trinity-fund/gamma-scalp/venv/bin/python3",
      cwd: "/root/trinity-fund/gamma-scalp",
      log_file: "/var/log/trinity/gamma-engine.log",
      out_file: "/var/log/trinity/gamma-engine-out.log",
      error_file: "/var/log/trinity/gamma-engine-error.log",
      restart_delay: 5000
    },
    {
      name: "gamma-gold-bot",
      script: "/root/trinity-fund/gamma-scalp/gold_bot.py",
      interpreter: "/root/trinity-fund/gamma-scalp/venv/bin/python3",
      cwd: "/root/trinity-fund/gamma-scalp",
      log_file: "/var/log/trinity/gamma-bot.log",
      out_file: "/var/log/trinity/gamma-bot-out.log",
      error_file: "/var/log/trinity/gamma-bot-error.log",
      restart_delay: 5000
    },
    {
      name: "gamma-dashboard",
      script: "/root/trinity-fund/gamma-scalp/dashboard/app.py",
      interpreter: "/root/trinity-fund/gamma-scalp/venv/bin/python3",
      cwd: "/root/trinity-fund/gamma-scalp",
      log_file: "/var/log/trinity/gamma-dashboard.log",
      out_file: "/var/log/trinity/gamma-dashboard-out.log",
      error_file: "/var/log/trinity/gamma-dashboard-error.log",
      restart_delay: 5000
    }
  ]
};
// Adăugăm serviciul de live feed
module.exports.apps.push({
  name: "live-feed-service",
  script: "/root/trinity-fund/live-feed-service.py",
  interpreter: "/root/trinity-fund/alpha-sniper/venv/bin/python3",
  cwd: "/root/trinity-fund",
  log_file: "/var/log/trinity/live-feed.log",
  restart_delay: 5000
});
