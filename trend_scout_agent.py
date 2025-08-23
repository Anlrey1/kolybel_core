# trend_scout_agent.py — мониторинг каналов и трендов (упрощённый)
import requests
import datetime
import logging
import time
from typing import List, Dict, Optional
from llm import ask_llm_with_context
from memory_core import MemoryCore
from config import (
    TELEGRAM_TOKEN,
    DEFAULT_MODEL,
    TREND_SOURCES,
    COMPETITOR_CHANNELS,
    SCRAPE_TIMEOUT,
    SCRAPE_RETRIES,
    MONITORING_INTERVAL,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChannelMonitor:
    def __init__(self, memory: MemoryCore):
        self.memory = memory
        self.competitors = self._parse_competitors()
        self.last_scan: Dict = {}
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "KolybelTrendScout/1.0"})

    def _parse_competitors(self) -> List[str]:
        return [f"@{c.strip().lstrip('@')}" for c in COMPETITOR_CHANNELS.split(",") if c.strip()]

    def _should_use_cache(self) -> bool:
        return bool(self.last_scan) and (datetime.datetime.now() - self.last_scan["timestamp"]).seconds < MONITORING_INTERVAL

    def monitor_competitors(self) -> Dict:
        if self._should_use_cache():
            return self.last_scan["data"]

        results = {}
        for channel in self.competitors:
            try:
                data = self._scrape_channel(channel)
                metrics = self._calculate_metrics(data)
                self._store_results(channel, data, metrics)
                results[channel] = metrics
            except Exception as e:
                logger.error(f"Ошибка мониторинга {channel}: {e}")
                results[channel] = {"error": str(e)}

        self.last_scan = {"timestamp": datetime.datetime.now(), "data": results}
        return results

    def _scrape_channel(self, channel: str) -> Dict:
        for attempt in range(1, SCRAPE_RETRIES + 1):
            try:
                # Заглушка
                return {
                    "channel": channel,
                    "last_posts": self._get_recent_posts(channel),
                    "subscribers": 12500,
                    "timestamp": datetime.datetime.now().isoformat(),
                }
            except Exception as e:
                if attempt == SCRAPE_RETRIES:
                    raise
                logger.warning(f"Попытка {attempt} для {channel}: {e}")
                time.sleep(2 ** attempt)

    def _get_recent_posts(self, channel: str) -> List[Dict]:
        return [
            {"views": 1500, "reactions": 45, "comments": 12, "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()},
            {"views": 3200, "reactions": 87, "comments": 23, "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=5)).isoformat()},
        ]

    def _calculate_metrics(self, data: Dict) -> Dict:
        posts = data.get("last_posts", [])
        if not posts:
            return {}

        total_views = sum(p.get("views", 0) for p in posts)
        total_reactions = sum(p.get("reactions", 0) for p in posts)
        total_comments = sum(p.get("comments", 0) for p in posts)

        # Простейшая частота
        dates = [datetime.datetime.fromisoformat(p["timestamp"]) for p in posts if "timestamp" in p]
        if len(dates) >= 2:
            days = (max(dates) - min(dates)).days or 1
            post_freq = len(posts) / days
        else:
            post_freq = len(posts)

        return {
            "avg_engagement": round(total_reactions / max(1, total_views), 4),
            "comment_ratio": round(total_comments / max(1, total_reactions), 2),
            "subscribers": data.get("subscribers", 0),
            "post_frequency": post_freq,
        }

    def _store_results(self, channel: str, raw_data: Dict, metrics: Dict) -> None:
        self.memory.store(
            document=f"Анализ {channel.lstrip('@')}",
            metadata={
                "type": "channel_analysis",
                "metrics": metrics,
                "sample_posts": raw_data.get("last_posts", [])[:3],
                "timestamp": raw_data["timestamp"],
            },
        )

class TrendScout:
    TREND_KEYWORDS = ["новый", "тренд", "разработка", "исследование", "технология"]

    def __init__(self, memory: Optional[MemoryCore] = None):
        self.memory = memory or MemoryCore()
        self.monitor = ChannelMonitor(self.memory)

    def fetch_trends(self) -> List[Dict]:
        self.monitor.monitor_competitors()
        trends: List[Dict] = []
        for source in TREND_SOURCES:
            try:
                data = self._fetch_source(source)
                trends.extend(self._process_source(source, data))
            except Exception as e:
                logger.error(f"Ошибка источника {source}: {e}")
        ranked = self._analyze_trends(trends)
        self._save_trends(ranked)
        return ranked

    def _fetch_source(self, source: str) -> Dict:
        if source.startswith("http"):
            r = self.monitor.session.get(source, timeout=SCRAPE_TIMEOUT)
            r.raise_for_status()
            return r.json()
        return {"text": source}

    def _process_source(self, source: str, data: Dict) -> List[Dict]:
        try:
            if source.startswith("http"):
                return [{"title": it.get("title", ""), "url": it.get("link", "")} for it in data.get("items", [])[:5]]
            llm_resp = ask_llm_with_context(f"Анализ трендов из текста: {data.get('text','')}", model=DEFAULT_MODEL)
            return [{"title": line.strip(), "source": "LLM"} for line in llm_resp.split("\n") if line.strip()]
        except Exception as e:
            logger.error(f"Ошибка обработки {source}: {e}")
            return []

    def _trend_score(self, text: str) -> float:
        words = text.lower().split()
        kw = sum(1 for w in words if w in self.TREND_KEYWORDS)
        length = len(words) / 10
        return kw * 0.7 + length * 0.3

    def _analyze_trends(self, trends: List[Dict]) -> List[Dict]:
        return sorted(
            trends,
            key=lambda x: self._trend_score(x.get("title", "")),
            reverse=True,
        )[:5]

    def _save_trends(self, trends: List[Dict]) -> None:
        for idx, t in enumerate(trends, 1):
            self.memory.store(
                document=t.get("title", ""),
                metadata={
                    "type": "trend",
                    "rank": idx,
                    "source": t.get("source", "RSS"),
                    "url": t.get("url", ""),
                    "timestamp": datetime.datetime.now().isoformat(),
                },
            )

def main():
    scout = TrendScout()
    print("🔍 Запуск мониторинга трендов...")
    for i, t in enumerate(scout.fetch_trends(), 1):
        print(f"{i}. {t['title']}" + (f"\n   🔗 {t['url']}" if t.get("url") else ""))

if __name__ == "__main__":
    main()
