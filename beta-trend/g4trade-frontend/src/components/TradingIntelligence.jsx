import { useState, useEffect } from 'react';

export default function TradingIntelligence() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, whalesRes, deltaRes] = await Promise.all([
          fetch('/api/trading/status'),
          fetch('/api/trading/whales'),
          fetch('/api/trading/delta')
        ]);
        
        const status = await statusRes.json();
        const whales = await whalesRes.json();
        const delta = await deltaRes.json();
        
        setData({ ...status, whales: whales.whales, deltaData: delta });
        setLoading(false);
      } catch (error) {
        console.error('Eroare la preluarea datelor de trading:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // Actualizare la 5 secunde
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="panel" style={{textAlign: 'center', color: 'var(--text-secondary)'}}>Se încarcă datele de inteligență...</div>;
  }

  const pressureColor = data?.deltaData?.signal?.includes('BUY') ? 'var(--accent-green)' : 
                        data?.deltaData?.signal?.includes('SELL') ? 'var(--accent-red)' : 'var(--text-secondary)';

  return (
    <div className="panel">
      <div className="panel-title">🧠 Trading Intelligence</div>
      
      {/* Delta Volume Analysis */}
      <div style={{marginBottom: '16px'}}>
        <div style={{fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px'}}>📊 Delta Volume Pressure</div>
        <div style={{
          background: 'var(--bg-tertiary)',
          padding: '12px',
          borderRadius: '6px',
          textAlign: 'center',
          border: '1px solid var(--border-color)'
        }}>
          <div style={{fontSize: '1.1rem', fontWeight: 'bold', color: pressureColor, letterSpacing: '1px'}}>
            {data?.deltaData?.signal || 'WAITING FOR DATA'}
          </div>
          {data?.deltaData?.delta && (
            <div style={{fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '6px'}}>
              Buy Vol: {data.deltaData.delta.buy_volume} | Sell Vol: {data.deltaData.delta.sell_volume}
            </div>
          )}
        </div>
      </div>

      {/* Whale Alerts */}
      <div>
        <div style={{fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '8px'}}>
          🐋 Whale Alerts ({data?.whale_stats?.total_whales || 0})
        </div>
        {data?.whales && data.whales.length > 0 ? (
          <div style={{maxHeight: '120px', overflowY: 'auto'}}>
            {data.whales.slice().reverse().map((whale, idx) => (
              <div key={idx} style={{
                background: 'var(--bg-tertiary)',
                padding: '8px',
                borderRadius: '4px',
                marginBottom: '4px',
                fontSize: '0.75rem',
                borderLeft: '3px solid var(--accent-blue)'
              }}>
                <div style={{color: 'var(--accent-blue)', fontWeight: 'bold'}}>
                  {whale.multiplier.toFixed(1)}x Volum Mediu
                </div>
                <div style={{color: 'var(--text-secondary)', fontSize: '0.7rem'}}>
                  Preț: ${whale.price} | {new Date(whale.timestamp * 1000).toLocaleTimeString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{color: 'var(--text-secondary)', fontSize: '0.75rem', textAlign: 'center', padding: '12px', background: 'var(--bg-tertiary)', borderRadius: '4px'}}>
            Nu s-au detectat activități de tip "Whale" recent.
          </div>
        )}
      </div>
    </div>
  );
}
