document.addEventListener("DOMContentLoaded", function () {
    function addSortButtonToTables() {
        let tables = document.querySelectorAll("table"); // ✅ 모든 테이블 가져오기

        tables.forEach((table, index) => {
            let headers = Array.from(table.rows[0]?.cells || []); // ✅ 테이블 헤더 가져오기
            let starIndex = headers.findIndex(cell => {
                let text = cell.innerText.trim().toLowerCase();
                return text === "star" || text === "likes";
            });

            if (starIndex === -1) return;  // ✅ "Star" 또는 "Likes" 컬럼이 없으면 패스

            // ✅ 이미 버튼이 있으면 추가하지 않음
            if (table.previousElementSibling && table.previousElementSibling.classList.contains("sort-button")) return;

            let sortButton = document.createElement("button");
            sortButton.innerText = "⭐ Sort by " + headers[starIndex].innerText.trim();
            sortButton.classList.add("sort-button");
            sortButton.style.cssText = "margin-bottom: 10px; padding: 8px 12px; background: #6200ea; color: white; border: none; cursor: pointer; border-radius: 5px;";

            table.parentNode.insertBefore(sortButton, table);

            sortButton.addEventListener("click", function () {
                let rows = Array.from(table.rows).slice(1);
                let isAscending = this.getAttribute("data-asc") === "true";

                rows.sort((rowA, rowB) => {
                    let valueA = parseInt(rowA.cells[starIndex]?.innerText.trim()) || 0;
                    let valueB = parseInt(rowB.cells[starIndex]?.innerText.trim()) || 0;
                    return isAscending ? valueA - valueB : valueB - valueA;
                });

                rows.forEach(row => table.appendChild(row));
                this.setAttribute("data-asc", !isAscending);
            });
        });
    }

    addSortButtonToTables(); // ✅ 초기 실행

    // ✅ SPA 페이지 이동 시 정렬 기능 다시 적용
    document.body.addEventListener("click", function () {
        setTimeout(addSortButtonToTables, 500);
    });
});
