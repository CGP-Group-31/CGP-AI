import json
from sqlalchemy import text
from app.core.db import engine

async def report_exist_for_week(elder_id: int, week_start: str, week_end: str) -> bool:
    sql = text(
        "SELECT TOP 1 1 FROM CareReports WHERE ElderID=:elder_id AND ReportType='weekly' "
        "AND PeriodStart=:week_start AND PeriodEnd=:week_end"
    )
    with engine.begin() as conn:
        row = conn.execute(sql, {"elder_id": elder_id, "week_start": week_start, "week_end": week_end}).fetchone()
    return row is not None


async def save_weekly_report(elder_id: int, week_start: str, week_end: str, report_json: dict, report_text: str, source_refs: list[dict]) -> int:
    sql_report = text("""
INSERT INTO CareReports(ElderID,ReportType,PeriodStart,PeriodEnd,ReportText,ReportJson)
OUTPUT INSERTED.ReportID
VALUES(:elder_id,'weekly',:week_start,:week_end,:report_text,:report_json)
""")
    sql_source = text("""
INSERT INTO ReportSources(ReportID,SourceType,SourceID)
VALUES(:report_id, :source_type, :source_id)
""")
    with engine.begin() as conn:
        report_id = conn.execute(sql_report, {
            "elder_id": elder_id,
            "week_start": week_start,
            "week_end": week_end,
            "report_text": report_text,
            "report_json": json.dumps(report_json, ensure_ascii=False)
        }).scalar_one()

        for src in source_refs:
            conn.execute(sql_source, {
                "report_id": report_id,
                "source_type": src["source_type"],
                "source_id": src["source_id"]
            })

    return int(report_id)