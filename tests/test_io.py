from datetime import date
from pathlib import Path

from app.models import Goal
from app.repositories import goals as goals_repo
from app.services import io_service, sessions_service, workouts_service


def test_export_then_import_roundtrip(conn, tmp_path: Path):
    goals_repo.create(conn, Goal(id=None, description="Lose 5 kg", metric="bodyweight_kg",
                                 start_value=80, target_value=75))
    workout = next(w for w in workouts_service.list_all(conn) if w.name == "Easy 5K")
    session = sessions_service.prefill_from_workout(
        conn, workout.id, date.today().isoformat()
    )
    session.sets[0].distance = 5.0
    session.sets[0].duration_sec = 1800
    sessions_service.save(conn, session)

    target = tmp_path / "out.json"
    io_service.export_json(conn, target)
    assert target.exists()
    payload = target.read_text()
    assert "Lose 5 kg" in payload

    # Now wipe DB and re-import.
    conn.execute("DELETE FROM session_log")
    conn.execute("DELETE FROM goal")
    conn.commit()
    assert goals_repo.list_all(conn) == []

    io_service.import_json(conn, target)
    restored_goals = goals_repo.list_all(conn)
    assert len(restored_goals) == 1
    assert restored_goals[0].description == "Lose 5 kg"
