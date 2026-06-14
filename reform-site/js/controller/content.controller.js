angular.module('app').controller('ContentController', function($scope, AllChapter, Content, PaginationContent, ChapterWiseContent, DeleteContent) {

    $scope.contents=[];
    $scope.currentPage = 0;
    $scope.numPerPage = 0;
    $scope.maxSize = 0;
    $scope.totalElement = 0;
    $scope.itemsPerPage = 20;
    $scope.chapter = null;
    Content.get(function (data) {
        $scope.contents = data.content;
        $scope.currentPage = data.number+1;
        $scope.numPerPage = data.size;
        $scope.maxSize = 20;
        $scope.currentPage = data.currentIndex;
        $scope.totalElement = data.totalElements;

    })
    AllChapter.get(function (data) {
        $scope.chapters = data;
    })
    $scope.pageChanged = function() {
        PaginationContent.get({page_num:$scope.currentPage},function (data) {
            console.log(data);
            $scope.contents = data.content;
        })
    };
    $scope.selectChapter = function() {
        console.log($scope.chapter);
        if($scope.chapter) {
            ChapterWiseContent.get({chapter:$scope.chapter.id}, function (data) {
                $scope.contents = data;
                $scope.currentPage = 0;
                $scope.numPerPage = 0;
                $scope.maxSize = 20;
                $scope.currentPage = 0;
                $scope.totalElement =0;

            })
        }

    };
    $scope.allData = function() {
        Content.get(function (data) {
            $scope.contents = data.content;
            $scope.currentPage = data.number+1;
            $scope.numPerPage = data.size;
            $scope.maxSize = 20;
            $scope.currentPage = data.currentIndex;
            $scope.totalElement = data.totalElements;

        })
    };
    $scope.deleteContent = function(id) {
        console.log(id);
        DeleteContent.delete({id:id},function (data) {
            console.log("deleted data: ");
            console.log(data);
            ChapterWiseContent.get({chapter:$scope.chapter.id}, function (data) {
                $scope.contents = data;
                $scope.currentPage = 0;
                $scope.numPerPage = 0;
                $scope.maxSize = 20;
                $scope.currentPage = 0;
                $scope.totalElement =0;

            })

        })
    };

}).controller('ContentAddController', function($scope, $rootScope, $stateParams,$state, Content, AllSection, MaxSerialBySection) {
    $scope.objects=[{section:{}}];
    $scope.section=null;
    $scope.sections={};
    $scope.hideAddMore = false;
    $scope.attachments = [];


    if($stateParams.id) {
        $scope.objects = [];
        $scope.hideAddMore = true;
        Content.get({id:$stateParams.id},function (data) {
            $scope.objects.push(data);
            $scope.section = data.section
        })
    }
    $scope.uploadFile = function ($index, $file) {
        console.log("clicked")
        $scope.$apply(function () {
            console.log($file)
            console.log($index)
            $scope.attachments[$index] = $rootScope.setFile($file);
            console.log( $scope.attachments[$index])
            // $scope.objects[$index].image  = $scope.attachment.file
            // $scope.objects[$index].fileContentType  = $scope.attachment.fileContentType
            // $scope.objects[$index].fileName  = $scope.attachment.fileName
            console.log($scope.attachments[$index])
        })

    };
    AllSection.get(function (data) {
        $scope.sections = data;
    })

    var onSaveSuccess = function (data) {
        $scope.globalMessage = "Chapter Added Successfully";
        $state.go('contents',null, {reload:true})
    };

    var onSaveError = function (result) {
        console.log(result);
        $state.formErrors = "Error Saving Chapter";
    };
    $scope.save = function() {
        console.log($scope.objects)
        angular.forEach($scope.objects, function(object, $index) {
            object.section.id = $scope.section.id;
            if(object.hasImage) {
                object.image  = $scope.attachments[$index].file
                object.fileContentType  = $scope.attachments[$index].fileContentType
                object.fileName  = $scope.attachments[$index].fileName

            }

        });
       Content.save($scope.objects, onSaveSuccess, onSaveError);
    };
    $scope.addMoreContent = function() {
        var serial = $scope.objects[$scope.objects.length-1].serial;
        console.log(serial)
        $scope.objects.push({section:{}, serial:serial+1});
    };
    $scope.removeContent = function($index) {
        $scope.objects.splice($index, 1);
    };
    $scope.changeSerial = function() {
        console.log($scope.section.id)
        MaxSerialBySection.get({sectionId:$scope.section.id}, function (data) {
            console.log(data);
            $scope.objects=[{section:{}, serial:data.serial+1}];
        })
    };
});

