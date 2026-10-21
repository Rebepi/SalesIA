import json
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from salesia.modules.analitica.application import historial, estadistica_descriptiva
from salesia.modules.analitica.application.contracts.historial import AnalysisRepeatRequest
from salesia.modules.analitica.application.contracts.estadistica_descriptiva import MeanRequest


def setup_repeat(extra=None, rows=None, version_data=None):
    user = SimpleNamespace(company_id=uuid4(), user_id=uuid4())
    source_id = uuid4()
    original = {"id": str(source_id), "name": "Media original", "dataset_id": str(uuid4()), "dataset_version": 3, "variable_name": "total_amount", "analysis_type": "mean", "status": "completed", "result": {"mean": "10.000000", "null_policy": "zero"}}
    original.update(extra or {})
    original_row = SimpleNamespace(id=source_id, data_json=json.dumps(original))
    version = SimpleNamespace(id=uuid4(), data_json=json.dumps(version_data if version_data is not None else {"rows": rows if rows is not None else [{"total_amount": "10"}, {"total_amount": "20"}, {"total_amount": None}]}))
    db = Mock()
    db.scalar.side_effect = [original_row, version]
    return user, source_id, original, db


def test_repeat_mean_preserves_null_policy_dataset_and_original():
    user, source_id, original, db = setup_repeat()
    result = historial.repeat_analysis(source_id, AnalysisRepeatRequest(new_version=3), user, db)
    assert result["result"]["mean"] == "10.000000"
    assert result["result"]["count"] == 3
    assert result["result"]["null_policy"] == "zero"
    assert result["dataset_version"] == 3
    assert result["id"] != str(source_id)
    assert result["parent_id"] == str(source_id)
    assert original["name"] == "Media original"
    assert "median" not in result["result"]
    db.add.assert_called_once()
    db.commit.assert_called_once()


def test_repeat_median_keeps_its_type_and_ignores_nulls():
    user, source_id, original, db = setup_repeat({"analysis_type": "median", "result": {"median": "20", "null_policy": "skip"}}, [{"total_amount": "10"}, {"total_amount": "20"}, {"total_amount": "100"}, {"total_amount": None}])
    result = historial.repeat_analysis(source_id, None, user, db)
    assert result["result"]["median"] == "20"
    assert result["result"]["null_count"] == 1
    assert result["result"]["count"] == 3
    assert "mean" not in result["result"]


@pytest.mark.parametrize("extra", [{"dataset_id": None}, {"status": "cancelled"}, {"analysis_type": "weighted_mean"}])
def test_non_reproducible_runs_fail_explicitly_without_writing(extra):
    user, source_id, original, db = setup_repeat(extra)
    with pytest.raises(HTTPException) as error:
        historial.repeat_analysis(source_id, None, user, db)
    assert error.value.status_code == 409
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_missing_dataset_file_does_not_produce_an_empty_success():
    user, source_id, original, db = setup_repeat(version_data={"storage_type": "private_file", "file_path": f"missing-{uuid4()}.json"})
    with pytest.raises(HTTPException) as error:
        historial.repeat_analysis(source_id, None, user, db)
    assert error.value.status_code == 409
    db.add.assert_not_called()


def test_listing_limits_rows_in_database_and_reports_full_count():
    user = SimpleNamespace(company_id=uuid4())
    db = Mock()
    db.scalar.return_value = 121
    db.scalars.return_value.all.return_value = [SimpleNamespace(data_json=json.dumps({"id": "one"}))]
    result = historial.list_analyses(None, "completed", 25, 50, user, db)
    assert result == {"items": [{"id": "one"}], "count": 121, "total_count": 121}
    query = db.scalars.call_args.args[0]
    compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
    assert "LIMIT 25" in compiled
    assert "OFFSET 50" in compiled
    assert "completed" in compiled
    assert str(user.company_id).replace("-", "") in compiled.replace("-", "")


def test_saved_mean_uses_resolved_dataset_version(monkeypatch):
    user = SimpleNamespace(company_id=uuid4(), user_id=uuid4())
    version = SimpleNamespace(id=uuid4(), version=7)
    monkeypatch.setattr(estadistica_descriptiva, "resolve_dataset_values", lambda **kwargs: ([Decimal("10"), Decimal("20")], 0, version))
    db = Mock()
    estadistica_descriptiva.post_mean_sync(MeanRequest(dataset_id=uuid4(), variable_name="total_amount"), user, db)
    saved = db.add.call_args.args[0]
    assert json.loads(saved.data_json)["dataset_version"] == 7
    assert saved.parent_id == version.id
