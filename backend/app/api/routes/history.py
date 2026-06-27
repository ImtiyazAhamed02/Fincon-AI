from fastapi import APIRouter, HTTPException
from app.db.client import SQLiteClient
import traceback
import json
from datetime import datetime, date

router = APIRouter()

@router.get("/sessions", summary="Get all analysis sessions")
def get_sessions():
    try:
        rows = SQLiteClient.execute(
            "SELECT id, session_id, ticker, company_name, recommendation, score, agents, summary, duration, created_at "
            "FROM analysis_history ORDER BY created_at DESC"
        )
        
        sessions = []
        for row in rows:
            try:
                # Parse created_at. SQLite stores it as a string.
                created_str = row["created_at"]
                
                if " " in created_str:
                    dt = datetime.strptime(created_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                else:
                    dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                
                try:
                    agents_list = json.loads(row["agents"])
                except Exception:
                    agents_list = [row["agents"]] if row["agents"] else []

                sessions.append({
                    "id": row["session_id"],
                    "ticker": row["ticker"],
                    "company": row["company_name"],
                    "rec": row["recommendation"],
                    "score": row["score"],
                    "agents": agents_list,
                    "date": dt.strftime("%Y-%m-%d"),
                    "time": dt.strftime("%I:%M %p"),
                    "summary": row["summary"],
                    "duration": row["duration"]
                })
            except Exception as e:
                print(f"Error parsing session row: {e}")
                continue
                
        return {"status": "success", "sessions": sessions}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", summary="Get dashboard stats based on history")
def get_stats():
    try:
        rows = SQLiteClient.execute("SELECT score, created_at FROM analysis_history")
        
        total_sessions = len(rows)
        today_str = date.today().isoformat()
        
        analyses_today = 0
        total_score = 0
        for row in rows:
            total_score += row["score"]
            created = row["created_at"] or ""
            if created.startswith(today_str):
                analyses_today += 1

        avg_confidence = int(total_score / total_sessions) if total_sessions > 0 else 0
        
        return {
            "status": "success",
            "stats": {
                "analyses_today": analyses_today,
                "avg_confidence": avg_confidence,
                "sessions_this_week": total_sessions
            }
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent-runs", summary="Get agent run logs for monitoring")
def get_agent_runs():
    """Returns recent agent execution logs from the agent_runs table."""
    try:
        rows = SQLiteClient.execute(
            "SELECT id, session_id, agent_name, input_data, output_data, confidence_score, created_at "
            "FROM agent_runs ORDER BY created_at DESC LIMIT 100"
        )
        
        runs = []
        for row in rows:
            try:
                created_str = row["created_at"] or ""
                if " " in created_str:
                    dt = datetime.strptime(created_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
                elif created_str:
                    dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                else:
                    dt = datetime.now()
                
                runs.append({
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "agent_name": row["agent_name"],
                    "input_data": row["input_data"],
                    "output_preview": (row["output_data"] or "")[:200],
                    "confidence_score": row["confidence_score"],
                    "date": dt.strftime("%Y-%m-%d"),
                    "time": dt.strftime("%I:%M %p"),
                })
            except Exception as e:
                print(f"Error parsing agent_run row: {e}")
                continue

        # Compute summary stats
        total_runs = len(runs)
        agent_counts = {}
        for r in runs:
            name = r["agent_name"]
            agent_counts[name] = agent_counts.get(name, 0) + 1

        return {
            "status": "success",
            "runs": runs,
            "total_runs": total_runs,
            "agent_counts": agent_counts,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
