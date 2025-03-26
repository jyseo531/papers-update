document.addEventListener("DOMContentLoaded", function () {
    function optimizeTableLoading() {
        let tables = document.querySelectorAll("table");

        tables.forEach((table, index) => {
            let rows = Array.from(table.querySelectorAll("tr"));
            let rowsPerRender = 50; // ✅ 한 번에 50개씩만 렌더링

            function renderRows(startIndex) {
                let endIndex = Math.min(startIndex + rowsPerRender, rows.length);
                for (let i = startIndex; i < endIndex; i++) {
                    rows[i].style.display = "";
                }

                if (endIndex < rows.length) {
                    setTimeout(() => renderRows(endIndex), 50); // ✅ 50ms 후 추가 렌더링 (부하 줄이기)
                }
            }

            rows.forEach(row => (row.style.display = "none")); // ✅ 초기에 숨김
            renderRows(0); // ✅ 첫 번째 블록 렌더링 시작
        });
    }

    optimizeTableLoading();
});
