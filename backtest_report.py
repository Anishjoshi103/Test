#!/usr/bin/env python3
import json, math, statistics, urllib.request, urllib.error
from datetime import datetime

TICKERS = ["TCS.NS","RELIANCE.NS","HDFCBANK.NS","INFY.NS","AAPL","NVDA","TSLA"]
HORIZON = 20


def fetch_chart(symbol, rng="5y"):
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range={rng}&includePrePost=false"
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)["chart"]["result"][0]


def valid_candles(r):
    q = r["indicators"]["quote"][0]
    out = []
    for i, t in enumerate(r.get("timestamp", [])):
        vals = [q["open"][i], q["high"][i], q["low"][i], q["close"][i], q["volume"][i]]
        if all(isinstance(x, (int, float)) and math.isfinite(x) and x > 0 for x in vals):
            out.append({"t": t, "o": vals[0], "h": vals[1], "l": vals[2], "c": vals[3], "v": vals[4]})
    return out


def sma(a, p): return sum(a[-p:]) / p

def ema(data, p):
    if len(data) < p: return None
    k = 2 / (p + 1)
    e = sum(data[:p]) / p
    for i in range(p, len(data)): e = data[i] * k + e * (1 - k)
    return e

def rsi(cl, p=14):
    if len(cl) <= p: return 50
    g = l = 0.0
    for i in range(1, p + 1):
        d = cl[i] - cl[i - 1]
        g += max(d, 0); l += max(-d, 0)
    ag, al = g / p, l / p
    for i in range(p + 1, len(cl)):
        d = cl[i] - cl[i - 1]
        ag = (ag * (p - 1) + max(d, 0)) / p
        al = (al * (p - 1) + max(-d, 0)) / p
    if al == 0: return 100
    return 100 - (100 / (1 + ag / al))

def macd(cl):
    e12 = [ema(cl[:i], 12) for i in range(12, len(cl) + 1)]
    e26 = [ema(cl[:i], 26) for i in range(26, len(cl) + 1)]
    n = min(len(e12), len(e26))
    m = [e12[-n + i] - e26[-n + i] for i in range(n)]
    s = [ema(m[:i], 9) for i in range(9, len(m) + 1)]
    sig = s[-1] if s else 0
    return {"macd": m[-1], "signal": sig, "hist": m[-1] - sig}

def atr(h,l,c,p=14):
    tr = [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1, len(c))]
    return sum(tr[-p:])/p

def calc(candles):
    c=[x['c'] for x in candles];h=[x['h'] for x in candles];l=[x['l'] for x in candles];v=[x['v'] for x in candles]
    last=c[-1];e20=ema(c,20);e50=ema(c,50);e200=ema(c,min(200,len(c)));R=rsi(c);M=macd(c);A=atr(h,l,c)
    pc=candles[-2];p=(pc['h']+pc['l']+pc['c'])/3;r1=2*p-pc['l'];r2=p+(pc['h']-pc['l']);vr=v[-1]/sma(v,min(20,len(v)))
    h52=max(c);l52=min(c);pos=((last-l52)/(h52-l52 if h52!=l52 else 1))*100
    score=0
    score += 10 if last>e200 else 0; score += 8 if last>e50 else 0; score += 7 if last>e20 else 0
    if 50<=R<65: score +=10
    elif 65<=R<75: score +=6
    elif 40<=R<50: score +=5
    score += 8 if M['hist']>0 else 0; score +=7 if M['macd']>M['signal'] else 0
    score += 15 if vr>2 else 10 if vr>1.5 else 5 if vr>1 else 0
    score += 10 if e20>e50 else 0; score += 10 if e50>e200 else 0
    score += 15 if pos>80 else 10 if pos>60 else 6 if pos>40 else 0
    score=min(100,score)
    verdict='BUY' if (score>=65 and R<75 and last>e200) else 'SELL' if (score<=35 or R>80 or (last<e200 and score<50)) else 'HOLD'
    sl=last-2*A; rs=sorted([x for x in [r1,r2] if x>last]); t1=rs[0] if rs else last*1.08
    return {"price":last,"verdict":verdict,"sl":sl,"t1":t1}

def evaluate(entry, future):
    hit_t=hit_s=None
    for i,c in enumerate(future,1):
        if hit_t is None and c['h']>=entry['t1']: hit_t=i
        if hit_s is None and c['l']<=entry['sl']: hit_s=i
    if hit_t and hit_s: return 'target_first' if hit_t<=hit_s else 'stop_first'
    if hit_t: return 'target_only'
    if hit_s: return 'stop_only'
    return 'none'

def write_report(lines):
    with open('BACKTEST_REPORT.md','w',encoding='utf-8') as f: f.write('\n'.join(lines)+'\n')

def run():
    rows=[]; failures=[]
    for t in TICKERS:
        try:
            c=valid_candles(fetch_chart(t))
        except Exception as e:
            failures.append((t, str(e)))
            continue
        if len(c)<260: continue
        for i in range(220, len(c)-HORIZON):
            sig=calc(c[:i+1]);
            if sig['verdict']!='BUY': continue
            fut=c[i+1:i+1+HORIZON]
            rows.append({'ticker':t,'outcome':evaluate(sig,fut),'ret':(fut[-1]['c']-sig['price'])/sig['price']*100})

    lines=["# StockSage Pro Backtesting Report","",f"Generated: {datetime.utcnow().isoformat()}Z",f"Universe: {', '.join(TICKERS)}",f"Horizon: {HORIZON} trading days",""]
    if not rows:
        lines += ["## Status","- No backtest metrics could be computed in this environment.","- Likely cause: outbound market-data requests blocked (proxy/tunnel policy).",""]
        if failures:
            lines.append("## Fetch Errors")
            for t,e in failures[:10]: lines.append(f"- {t}: {e}")
        lines += ["", "## How to Run Locally", "1. Ensure internet access to Yahoo Finance endpoints.", "2. Run: `python3 backtest_report.py`", "3. Review generated `BACKTEST_REPORT.md` metrics."]
        write_report(lines)
        print('Wrote BACKTEST_REPORT.md (environment-limited mode)')
        return

    total=len(rows); hit_t=sum(1 for r in rows if r['outcome'] in ('target_first','target_only')); hit_s=sum(1 for r in rows if r['outcome'] in ('stop_first','stop_only')); tf=sum(1 for r in rows if r['outcome']=='target_first'); pos=sum(1 for r in rows if r['ret']>0)
    lines += ["## Aggregate BUY Results",f"- BUY signals tested: {total}",f"- Target hit rate: {hit_t/total*100:.1f}%",f"- Stop hit rate: {hit_s/total*100:.1f}%",f"- Target-before-stop rate: {tf/total*100:.1f}%",f"- Positive 20D return rate: {pos/total*100:.1f}%",f"- Median 20D return: {statistics.median([r['ret'] for r in rows]):.2f}%",""]
    write_report(lines)
    print('Wrote BACKTEST_REPORT.md with real metrics')

if __name__=='__main__': run()
