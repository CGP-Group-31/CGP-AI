import json
from sqlalchemy import text
from app.core.db import engine


async def report_exist_for_day(elder_id: int, report_date:str)->bool:
    sql = text(
        '''SELECT TOP 1 1 FROM CareReports WHERE ElderID= :elder_id AND ReportType='daily' AND PeriodStart= :report_date AND PeriodEnd = :report_date'''
    )

    with engine.begin() as conn:
        row = conn.execute(sql, {
            "elder_id": elder_id,
            "report_date": report_date
        }).fetchone()

    return row is not None



async def get_checkin_runs_for_day(elder_id: int, report_date: str) -> list[dict]:
    sql = text("""
        SELECT
            c.RunID,
            c.Status,
            c.WindowType,
            c.LocalDate,
            c.PlannedAt,
            c.TriggeredAt,
            c.CompletedAt,
            m.Content AS UserResponse,
            mt.MoodName AS DetectedMood,
            c.Notes
        FROM CheckInRuns c
        LEFT JOIN ChatThreads ct
            ON ct.RelatedRunID = c.RunID
        LEFT JOIN ChatMessages m
            ON m.ThreadID = ct.ThreadID
            AND m.Role = 'elder'
        LEFT JOIN MoodTypes mt
            ON m.DetectedMoodID = mt.MoodID
        WHERE c.ElderID = :elder_id
          AND c.LocalDate = :report_date
        ORDER BY c.PlannedAt ASC, m.CreatedAt ASC
    """)

    with engine.begin() as conn:
        rows = conn.execute(sql, {
            "elder_id": elder_id,
            "report_date": report_date,
        }).mappings().all()

    return [dict(r) for r in rows]



async def save_daily_report(elder_id: int, report_date:str,report_json:dict, report_text:str,source_refs: list[dict])->int:
    sql_report = text(
        '''
INSERT INTO CareReports(ElderID,ReportType,PeriodStart,PeriodEnd,ReportText,ReportJson)
OUTPUT INSERTED.ReportID 
VALUES(:elder_id,'daily',:period_start,:period_end,:report_text,:report_json)
''')
    
    sql_source = text('''
        INSERT INTO ReportSources(ReportID,SourceType,SourceID)
        VALUES(:report_id, :source_type, :source_id)
        ''')
    

    with engine.begin() as conn:
        report_id = conn.execute(sql_report, {
            "elder_id": elder_id,
            "period_start": report_date,
            "period_end": report_date,
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











