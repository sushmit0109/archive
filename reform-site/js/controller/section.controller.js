angular.module('app').controller('SectionController', function($scope,Section, PaginationSection) {

    $scope.sections=[];
    $scope.currentPage = 0;
    $scope.numPerPage = 0;
    $scope.maxSize = 0;
    $scope.totalElement = 0;
    $scope.itemsPerPage = 20;
    Section.get(function (data) {
        console.log(data)
        $scope.sections = data.content;
        $scope.currentPage = data.number+1;
        $scope.numPerPage = data.size;
        $scope.maxSize = 20;
        $scope.currentPage = data.currentIndex;
        $scope.totalElement = data.totalElements;

    })
    $scope.pageChanged = function() {
        PaginationSection.get({page_num:$scope.currentPage},function (data) {
            console.log(data);
            $scope.sections = data.content;
        })
    };
}).controller('SectionAddController', function($scope,$stateParams,$state, Section, AllChapter) {
    $scope.object={};
    $scope.sections=[{chapter:{}}];
    $scope.chapters={};

    if($stateParams.id) {
        Section.get({id:$stateParams.id},function (data) {
            $scope.object = data;
            $scope.sections = [$scope.object]

        })
    }

    AllChapter.get(function (data) {
        $scope.chapters = data;
    })
    if($stateParams.id) {
        Section.get({id:$stateParams.id},function (data) {
            $scope.section = data;
        })
    }

    $scope.addMoreContent = function() {
        var serial = $scope.sections[$scope.sections.length-1].serial;
        console.log(serial)
        $scope.sections.push({chapter:{},serial:serial+1});
    };
    $scope.removeContent = function($index) {
        $scope.sections.splice($index, 1);
    };
    var onSaveSuccess = function (data) {
        $scope.globalMessage = "Chapter Added Successfully";
        $state.go('sections',null, {reload:true})
    };

    var onSaveError = function (result) {
        console.log(result);
        $state.formErrors = "Error Saving Chapter";
    };
    $scope.save = function() {
        console.log($scope.itemType)
        angular.forEach($scope.sections, function(object, $index) {
            object.chapter.id = $scope.object.chapter.id;
        });
        console.log($scope.sections)
        Section.save($scope.sections, onSaveSuccess, onSaveError);
    };
});

