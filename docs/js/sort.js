document.addEventListener("DOMContentLoaded", function () {
    function addSortButtonToTables() {
        let tables = document.querySelectorAll("table"); // 모든 테이블 가져오기

        tables.forEach((table, index) => {
            let headers = Array.from(table.rows[0].cells); // 테이블 헤더 가져오기
            let starIndex = headers.findIndex(cell => 
                cell.innerText.trim().toLowerCase() === "star" || 
                cell.innerText.trim().toLowerCase() === "likes"
            ); 

            // Star 또는 Likes 컬럼이 없는 테이블이면 버튼 추가 X
            if (starIndex === -1) return;  

            // 이미 버튼이 있으면 추가하지 않음
            if (table.previousElementSibling && table.previousElementSibling.id === `sortButton-${index}`) return;

            let sortButton = document.createElement("button");
            sortButton.innerText = "⭐ Sort by " + headers[starIndex].innerText.trim();
            sortButton.id = `sortButton-${index}`;
            sortButton.style.cssText = "margin-bottom: 10px; padding: 8px 12px; background: #6200ea; color: white; border: none; cursor: pointer; border-radius: 5px;";

            table.parentNode.insertBefore(sortButton, table);

            sortButton.addEventListener("click", function () {
                let rows = Array.from(table.rows).slice(1); // 첫 번째 행(헤더) 제외
                let isAscending = this.getAttribute("data-asc") === "true";  // 정렬 방향 확인

                rows.sort((rowA, rowB) => {
                    let valueA = parseInt(rowA.cells[starIndex]?.innerText.trim()) || 0;
                    let valueB = parseInt(rowB.cells[starIndex]?.innerText.trim()) || 0;
                    return isAscending ? valueA - valueB : valueB - valueA;
                });

                rows.forEach(row => table.appendChild(row)); // 정렬된 행 적용
                this.setAttribute("data-asc", !isAscending); // 방향 토글
            });
        });
    }

    addSortButtonToTables(); // 초기에 실행

    // SPA(Single Page Application) 구조 대응 → 페이지 이동할 때도 버튼 다시 추가
    document.body.addEventListener("click", function () {
        setTimeout(addSortButtonToTables, 500);  // 페이지 변경 후 버튼 다시 추가
    });
});
