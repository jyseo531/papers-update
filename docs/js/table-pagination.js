document.addEventListener("DOMContentLoaded", function () {
    function addPaginationToTables() {
        let tables = document.querySelectorAll("table"); // 모든 테이블 가져오기

        tables.forEach((table, index) => {
            if (table.id) return; // 이미 ID가 있으면 패스 (중복 방지)
            table.id = `table-${index}`; 

            let rowsPerPage = 300; // ✅ 한 페이지에 10개씩 표시
            let rows = Array.from(table.querySelectorAll("tbody tr"));
            let numPages = Math.ceil(rows.length / rowsPerPage);

            if (numPages <= 1) return; // 데이터가 적으면 페이지네이션 필요 없음

            // ✅ 페이지네이션 컨트롤 버튼 추가
            let paginationContainer = document.createElement("div");
            paginationContainer.className = "pagination-container";
            table.parentNode.insertBefore(paginationContainer, table.nextSibling);

            for (let i = 0; i < numPages; i++) {
                let pageButton = document.createElement("button");
                pageButton.innerText = i + 1;
                pageButton.className = "pagination-button";
                pageButton.onclick = function () {
                    showPage(i);
                };
                paginationContainer.appendChild(pageButton);
            }

            function showPage(pageNum) {
                let start = pageNum * rowsPerPage;
                let end = start + rowsPerPage;
                rows.forEach((row, index) => {
                    row.style.display = index >= start && index < end ? "" : "none";
                });

                // ✅ 선택된 버튼 스타일 적용
                document.querySelectorAll(".pagination-button").forEach(btn => btn.style.background = "#eee");
                paginationContainer.children[pageNum].style.background = "#6200ea";
            }

            showPage(0); // 첫 페이지 표시
        });
    }

    addPaginationToTables(); // 초기에 실행

    // SPA(Single Page Application) 대응 → 페이지 이동 후 테이블 업데이트
    document.body.addEventListener("click", function () {
        setTimeout(addPaginationToTables, 500);
    });
});
