document.addEventListener("DOMContentLoaded", function () {
    function addPaginationToTables() {
        let tables = document.querySelectorAll("table");
        let decodedURL = decodeURIComponent(window.location.pathname);

        tables.forEach((table, index) => {
            if (table.dataset.paginated) return;
            table.dataset.paginated = "true";

            let rows = Array.from(table.querySelectorAll("tr"));
            let rowsPerPage = 10;
            let numPages = Math.ceil((rows.length - 1) / rowsPerPage);
            let maxPageButtons = 10;
            
            if (numPages <= 1) return;

            let paginationContainer = document.createElement("div");
            paginationContainer.className = "pagination-container";
            table.parentNode.insertBefore(paginationContainer, table.nextSibling);

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

            let currentPageGroup = 0;
            let timeoutId = null;

            function renderPageButtons() {
                pageButtonsContainer.innerHTML = "";
                let startPage = currentPageGroup * maxPageButtons;
                let endPage = Math.min(startPage + maxPageButtons, numPages);

                for (let i = startPage; i < endPage; i++) {
                    let pageButton = document.createElement("button");
                    pageButton.innerText = i + 1;
                    pageButton.className = "pagination-button";
                    pageButton.onclick = function () {
                        showPage(i);
                    };
                    pageButtonsContainer.appendChild(pageButton);
                }

                prevButton.style.display = (numPages > maxPageButtons) ? "inline-block" : "none";
                nextButton.style.display = (numPages > maxPageButtons) ? "inline-block" : "none";

                prevButton.disabled = currentPageGroup === 0;
                nextButton.disabled = endPage >= numPages;
            }

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

            function showPage(pageNum) {
                clearTimeout(timeoutId); // 기존 타이머 제거
                timeoutId = setTimeout(() => { // 브라우저가 처리할 시간을 확보
                    let start = pageNum * rowsPerPage + 1;
                    let end = start + rowsPerPage;
                    rows.forEach((row, index) => {
                        row.style.display = index === 0 || (index >= start && index < end) ? "" : "none";
                    });

                    document.querySelectorAll(".pagination-button").forEach(btn => btn.style.background = "#eee");
                    if (pageButtonsContainer.children[pageNum % maxPageButtons]) {
                        pageButtonsContainer.children[pageNum % maxPageButtons].style.background = "#6200ea";
                    }
                }, 50); // 50ms 딜레이를 줘서 로딩 속도 최적화
            }

            renderPageButtons();
            showPage(0);
        });
    }

    addPaginationToTables(); 

    document.body.addEventListener("click", function () {
        setTimeout(addPaginationToTables, 500);
    });
});
