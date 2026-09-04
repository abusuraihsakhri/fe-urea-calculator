"""
Tests for FEUrea Calculator core functionality.
"""
import pytest
from fe_urea import calculate_fe_urea, calculate_metrics, process_batch, ValidationError


class TestCalculateFeUrea:
    """Tests for the core FEUrea calculation function."""

    def test_prerenal_azotemia(self):
        """FEUrea < 35% suggests prerenal azotemia."""
        # Typical prerenal values: low FEUrea
        result = calculate_fe_urea(
            serum_creatinine=1.0,
            urine_creatinine=100.0,
            serum_urea=20.0,
            urine_urea=100.0
        )
        # FEUrea = (100 * 1.0) / (20 * 100) * 100 = 5.0%
        assert result["fe_urea_percent"] == 5.0
        assert result["classification"] == "Prerenal Azotemia"
        assert "prerenal" in result["clinical_recommendation"].lower()

    def test_acute_tubular_necrosis(self):
        """FEUrea >= 35% suggests ATN."""
        # Typical ATN values: high FEUrea
        result = calculate_fe_urea(
            serum_creatinine=2.0,
            urine_creatinine=50.0,
            serum_urea=30.0,
            urine_urea=300.0
        )
        # FEUrea = (300 * 2.0) / (30 * 50) * 100 = 40.0%
        assert result["fe_urea_percent"] == 40.0
        assert result["classification"] == "Acute Tubular Necrosis / Intrinsic Renal Disease"
        assert "ATN" in result["clinical_recommendation"] or "intrinsic" in result["clinical_recommendation"].lower()

    def test_boundary_value_35_percent(self):
        """Test the 35% boundary between prerenal and ATN."""
        # Calculate values that give exactly 35%
        result = calculate_fe_urea(
            serum_creatinine=1.0,
            urine_creatinine=100.0,
            serum_urea=20.0,
            urine_urea=175.0
        )
        # FEUrea = (175 * 1.0) / (20 * 100) * 100 = 87.5%
        # Actually let me recalculate: need values that give 35%
        # 35 = (urine_urea * 1.0) / (20 * 100) * 100
        # 35 = urine_urea / 20
        # urine_urea = 700
        result = calculate_fe_urea(
            serum_creatinine=1.0,
            urine_creatinine=100.0,
            serum_urea=20.0,
            urine_urea=700.0
        )
        assert result["fe_urea_percent"] == 35.0
        assert result["classification"] == "Acute Tubular Necrosis / Intrinsic Renal Disease"

    def test_negative_serum_creatinine_raises_error(self):
        """Negative values should raise ValidationError."""
        with pytest.raises(ValidationError, match="serum_creatinine must be positive"):
            calculate_fe_urea(serum_creatinine=-1.0, urine_creatinine=100.0,
                            serum_urea=20.0, urine_urea=200.0)

    def test_zero_urine_creatinine_raises_error(self):
        """Zero values should raise ValidationError."""
        with pytest.raises(ValidationError, match="urine_creatinine must be positive"):
            calculate_fe_urea(serum_creatinine=1.0, urine_creatinine=0.0,
                            serum_urea=20.0, urine_urea=200.0)

    def test_non_numeric_input_raises_error(self):
        """Non-numeric inputs should raise ValidationError."""
        with pytest.raises(ValidationError, match="serum_creatinine must be numeric"):
            calculate_fe_urea(serum_creatinine="abc", urine_creatinine=100.0,
                            serum_urea=20.0, urine_urea=200.0)

    def test_result_contains_all_fields(self):
        """Result should contain all expected fields."""
        result = calculate_fe_urea(
            serum_creatinine=1.2,
            urine_creatinine=120.0,
            serum_urea=25.0,
            urine_urea=250.0
        )
        assert "tool" in result
        assert "fe_urea_percent" in result
        assert "classification" in result
        assert "clinical_recommendation" in result
        assert "inputs" in result
        assert result["tool"] == "fe-urea-calculator"


class TestCalculateMetrics:
    """Tests for the legacy compatibility wrapper."""

    def test_with_v1_v2_v3_params(self):
        """Legacy v1, v2, v3 parameters should work."""
        result = calculate_metrics(v1=1.0, v2=100.0, v3=20.0)
        assert "fe_urea_percent" in result
        assert "classification" in result

    def test_with_named_params(self):
        """Named parameters should work directly."""
        result = calculate_metrics(
            serum_creatinine=1.0,
            urine_creatinine=100.0,
            serum_urea=20.0,
            urine_urea=200.0
        )
        assert "fe_urea_percent" in result

    def test_with_no_params(self):
        """Default values should produce a valid result."""
        result = calculate_metrics()
        assert "fe_urea_percent" in result
        assert "classification" in result


class TestProcessBatch:
    """Tests for batch CSV processing."""

    def test_batch_processing(self, tmp_path):
        """Batch processing should handle valid CSV."""
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text(
            "Patient_ID,serum_creatinine,urine_creatinine,serum_urea,urine_urea\n"
            "PT-001,1.2,120.0,25.0,250.0\n"
            "PT-002,0.9,150.0,18.0,180.0\n",
            encoding="utf-8"
        )
        process_batch(str(csv_in), str(csv_out))
        assert csv_out.exists()
        content = csv_out.read_text(encoding="utf-8")
        assert "PT-001" in content
        assert "fe_urea_percent" in content

    def test_batch_with_invalid_rows(self, tmp_path):
        """Batch processing should handle invalid rows gracefully."""
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text(
            "Patient_ID,serum_creatinine,urine_creatinine,serum_urea,urine_urea\n"
            "PT-001,1.2,120.0,25.0,250.0\n"
            "PT-002,-1.0,150.0,18.0,180.0\n",
            encoding="utf-8"
        )
        process_batch(str(csv_in), str(csv_out))
        assert csv_out.exists()
        content = csv_out.read_text(encoding="utf-8")
        assert "PT-001" in content
        assert "PT-002" in content
        assert "INVALID_INPUT" in content

    def test_batch_file_not_found(self, tmp_path):
        """Batch processing should handle missing input file."""
        import sys
        from io import StringIO
        csv_out = tmp_path / "out.csv"
        # This should exit with error
        with pytest.raises(SystemExit):
            process_batch("nonexistent_file.csv", str(csv_out))
