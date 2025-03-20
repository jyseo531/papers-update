document.addEventListener("DOMContentLoaded", function() {
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                loadMoreData(); // 추가 데이터 로드
            }
        });
    }, { rootMargin: '100px' });

    // 스크롤 트리거 요소가 있는지 확인 후 감시 시작
    const scrollTrigger = document.querySelector("#scroll-trigger");
    if (scrollTrigger) {
        observer.observe(scrollTrigger);
    }

    async function loadMoreData() {
        // 데이터 로드 로직 (여기에 페이지네이션 API 요청 or 새로운 데이터 추가 코드 넣기)
        console.log("Loading more data...");
    }
});
