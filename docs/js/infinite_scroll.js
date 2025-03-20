// document.addEventListener("DOMContentLoaded", function() {
//     const observer = new IntersectionObserver(entries => {
//         entries.forEach(entry => {
//             if (entry.isIntersecting) {
//                 loadMoreData(); // 추가 데이터 로드
//             }
//         });
//     }, { rootMargin: '100px' });

//     // 스크롤 트리거 요소가 있는지 확인 후 감시 시작
//     const scrollTrigger = document.querySelector("#scroll-trigger");
//     if (scrollTrigger) {
//         observer.observe(scrollTrigger);
//     }

//     async function loadMoreData() {
//         // 데이터 로드 로직 (여기에 페이지네이션 API 요청 or 새로운 데이터 추가 코드 넣기)
//         console.log("Loading more data...");
//     }
// });

document.addEventListener("DOMContentLoaded", function() {
    let isScrolling = false;
    let isLoading = false;

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !isLoading && isScrolling) {
                loadMoreData();
            }
        });
    }, { rootMargin: '100px' });

    const scrollTrigger = document.querySelector("#scroll-trigger");
    if (scrollTrigger) {
        observer.observe(scrollTrigger);
    }

    // 스크롤 이벤트 감지
    let scrollTimeout;
    window.addEventListener("scroll", () => {
        isScrolling = true;
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            isScrolling = false; // 사용자가 스크롤을 멈추면 로드 중단
        }, 300); // 300ms 동안 스크롤 이벤트가 없으면 중단
    });

    async function loadMoreData() {
        isLoading = true;
        console.log("Loading more data...");
        
        // 여기에 AJAX 요청 또는 데이터 추가 코드 삽입
        await new Promise(resolve => setTimeout(resolve, 1000)); // 가짜 데이터 로드 딜레이
        
        isLoading = false;
    }
});
