angular.module('app')
    .controller('NoticeController', function ($http, $scope, $rootScope, $state, Notice) {
        $scope.noticeList = [];
        $scope.maxSize = 5;
        $scope.currentPage = 1;
        $scope.totalElement = 0;
        $scope.itemsPerPage = 10;
        $scope.serial = 0;
        $scope.loadData = function () {
            Notice.get({pageNumber: $scope.currentPage}, function (response) {
                console.log(response)
                $scope.noticeList = response.content;
                $scope.numPerPage = response.size;
                $scope.maxSize = 20;
                $scope.currentPage = response.number+1;
                $scope.totalElement = response.totalElements;
                $scope.serial = $scope.itemsPerPage*($scope.currentPage-1);
            })
        }
        $scope.loadData();
        $scope.pageChanged = function() {
            $scope.loadData();
        };
    })
    .controller('NoticeViewController', function ($http, $scope, $rootScope, $state, $stateParams, $filter, Notice) {
        $scope.notice = {};
        $scope.image = {};
        $scope.pdf = {};
        $scope.fieldKey=$rootScope.fieldKey;

        if ($stateParams.id) {
            Notice.get({id: $stateParams.id}, function (response) {
                var date = new Date(response.publishDate);
                // response.publishDate = date.getFullYear() + "-" + (date.getMonth()+1) + "-" + date.getDate();
                $scope.notice = response;
                console.log('Controller response: ' + response);
            })
        };

        $scope.getIframeSrc = function (pdfUrl) {
            console.log({pdfUrl})
            return './pdfs/attachment/' + pdfUrl;
        };
});

