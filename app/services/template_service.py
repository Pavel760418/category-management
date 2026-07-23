from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation


class TemplateService:
    def __init__(self, template_dir: str):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.header_fill = PatternFill("solid", fgColor="1F4E78")
        self.header_font = Font(color="FFFFFF", bold=True)
        self.note_fill = PatternFill("solid", fgColor="FFF2CC")

    def _decorate_headers(self, ws, row, headers):
        for idx, h in enumerate(headers, start=1):
            c = ws.cell(row=row, column=idx, value=h)
            c.fill = self.header_fill
            c.font = self.header_font
            c.alignment = Alignment(horizontal="center", vertical="center")
            ws.column_dimensions[c.column_letter].width = 18

    def create_sku_template(self):
        path = self.template_dir / "sku_upload_template.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "SKU Upload"
        headers = ["sku_code", "sku_name", "category", "subcategory", "sales_value", "sales_qty", "cogs_value", "stock_qty", "purchase_price", "shelf_meters", "prior_sales_value", "prior_sales_qty", "prior_gp_value", "store_name", "format_name", "period_months", "current_role"]
        self._decorate_headers(ws, 3, headers)
        ws["A1"] = "Шаблон загрузки SKU-данных"
        ws["A2"] = "Обязательные поля: sku_code, sku_name, category, subcategory, sales_value, sales_qty, cogs_value, stock_qty, purchase_price"
        sample = ["SKU-001", "Корм сухой для кошек 1 кг", "Товары для животных", "Корма", 125000, 420, 86000, 90, 955, 2.5, 118000, 390, 30000, "Ленинград", "Супермаркет", 6, "Базовый"]
        for i, v in enumerate(sample, start=1):
            ws.cell(row=4, column=i, value=v)
        dv = DataValidation(type="whole", operator="between", formula1=1, formula2=12, allow_blank=True)
        ws.add_data_validation(dv)
        dv.add("P4:P5000")
        wb.save(path)
        return path

    def create_competitor_template(self):
        path = self.template_dir / "competitor_upload_template.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "Competitors"
        headers = ["competitor_name", "category", "price_index", "width_sku", "depth", "shelf_meters", "stm_share", "promo_share", "comments"]
        self._decorate_headers(ws, 3, headers)
        ws["A1"] = "Шаблон конкурентного мониторинга"
        ws["A2"] = "Обязательные поля: competitor_name, category, price_index"
        sample = ["Конкурент А", "Товары для животных", 1.04, 220, 6, 5.5, 0.12, 0.18, "Широкий ассортимент по кормам"]
        for i, v in enumerate(sample, start=1):
            ws.cell(row=4, column=i, value=v)
        wb.save(path)
        return path

    def create_goals_template(self):
        path = self.template_dir / "goals_upload_template.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "Goals"
        headers = ["metric_name", "target_3m", "target_6m", "notes"]
        self._decorate_headers(ws, 3, headers)
        ws["A1"] = "Шаблон целевых KPI"
        ws["A2"] = "Примеры metric_name: turnover, gross_profit, margin_pct, stock_days, sku_count, lfl_sales, inventory_turnover, revenue_per_shelf"
        sample_rows = [
            ["turnover", 2700000, 5500000, "Цель по обороту"],
            ["stock_days", 21, 21, "Целевые дни запаса"],
            ["sku_count", 50, 50, "Целевое количество SKU"],
        ]
        for r, vals in enumerate(sample_rows, start=4):
            for c, v in enumerate(vals, start=1):
                ws.cell(row=r, column=c, value=v)
        wb.save(path)
        return path
