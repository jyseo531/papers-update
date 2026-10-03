document.addEventListener("DOMContentLoaded", function () {
    function initializeTable(table) {
        let rows = Array.from(table.querySelectorAll("tr")).slice(1); // 첫 번째 행(헤더) 제외
        let headers = table.querySelectorAll("th");
        let paginationContainer = document.createElement("div");
        paginationContainer.className = "pagination-container";
        table.parentNode.insertBefore(paginationContainer, table.nextSibling);

        let rowsPerPage = 10;
        let currentPage = 0;
        let numPages = Math.ceil(rows.length / rowsPerPage);
        let maxPageButtons = 10;
        let currentPageGroup = 0;

        let sortedRows = [...rows]; // ✅ 정렬된 데이터를 저장할 배열

        function renderPageButtons() {
            pageButtonsContainer.innerHTML = "";
            let startPage = currentPageGroup * maxPageButtons;
            let endPage = Math.min(startPage + maxPageButtons, numPages);

            for (let i = startPage; i < endPage; i++) {
                let pageButton = document.createElement("button");
                pageButton.innerText = i + 1;
                pageButton.className = "pagination-button";
                pageButton.onclick = function () {
                    currentPage = i;
                    renderPage(i);
                };
                pageButtonsContainer.appendChild(pageButton);
            }

            prevButton.style.display = numPages > maxPageButtons ? "inline-block" : "none";
            nextButton.style.display = numPages > maxPageButtons ? "inline-block" : "none";

            prevButton.disabled = currentPageGroup === 0;
            nextButton.disabled = endPage >= numPages;
        }

        function renderPage(pageNum) {
            let start = pageNum * rowsPerPage;
            let end = start + rowsPerPage;

            rows.forEach(row => row.style.display = "none"); // ✅ 모든 행 숨김
            sortedRows.slice(start, end).forEach(row => row.style.display = ""); // ✅ 선택된 페이지 행만 표시

            document.querySelectorAll(".pagination-button").forEach(btn => btn.style.background = "#eee");
            if (pageButtonsContainer.children[pageNum % maxPageButtons]) {
                pageButtonsContainer.children[pageNum % maxPageButtons].style.background = "#6200ea";
            }
        }

        function applySorting(columnIndex, isAscending) {
            sortedRows.sort((rowA, rowB) => {
                let valueA = parseInt(rowA.cells[columnIndex].innerText.trim()) || 0;
                let valueB = parseInt(rowB.cells[columnIndex].innerText.trim()) || 0;
                return isAscending ? valueA - valueB : valueB - valueA;
            });

            currentPage = 0; // ✅ 정렬 후 첫 페이지로 이동
            numPages = Math.ceil(sortedRows.length / rowsPerPage);
            renderPage(currentPage);
            renderPageButtons();
        }

        headers.forEach((header, columnIndex) => {
            if (header.innerText.toLowerCase() === "star" || header.innerText.toLowerCase() === "likes") {
                let sortButton = document.createElement("button");
                sortButton.innerText = "🔼 Sort";
                sortButton.className = "sort-button";
                header.appendChild(sortButton);
                let isAscending = true;

                sortButton.addEventListener("click", function () {
                    isAscending = !isAscending;
                    applySorting(columnIndex, isAscending);
                });
            }
        });

        let prevButton = document.createElement("button");
        prevButton.innerText = "◀ Prev";
        prevButton.className = "pagination-prev";
        paginationContainer.appendChild(prevButton);

        let pageButtonsContainer = document.createElement("span");
        pageButtonsContainer.className = "page-buttons";
        paginationContainer.appendChild(pageButtonsContainer);

        let nextButton = document.createElement("button");
        nextButton.innerText = "Next ▶";
        nextButton.className = "pagination-next";
        paginationContainer.appendChild(nextButton);

        prevButton.addEventListener("click", function () {
            if (currentPageGroup > 0) {
                currentPageGroup--;
                renderPageButtons();
            }
        });

        nextButton.addEventListener("click", function () {
            if ((currentPageGroup + 1) * maxPageButtons < numPages) {
                currentPageGroup++;
                renderPageButtons();
            }
        });

        renderPageButtons();
        renderPage(0);
    }

    let tables = document.querySelectorAll("table");
    tables.forEach(table => initializeTable(table));
});
