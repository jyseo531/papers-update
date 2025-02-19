$(document).ready(function() {
    // 모든 테이블에 DataTables 적용
    $('table').DataTable({
        "order": [[ 0, "desc" ]],  // 첫 번째 열 기준 내림차순 정렬
        "paging": false,           // 페이징 비활성화
        "info": false,             // 하단 정보 비활성화
        "autoWidth": false,        // 자동 너비 조절 비활성화
        "language": {
            "search": "검색: ",      // 검색창 한글화
            "zeroRecords": "검색 결과가 없습니다."
        }
    });
});