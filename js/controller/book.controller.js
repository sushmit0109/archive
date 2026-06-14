angular.module('app').controller('BookController', function($scope,Book) {

    $scope.books=[];
    $scope.currentPage = 0;
    $scope.numPerPage = 0;
    $scope.maxSize = 0;
    $scope.totalElement = 0;
    Book.get(function (data) {
        console.log(data)
        $scope.books = data.content;
        $scope.numPerPage = data.size;
        $scope.maxSize = 20;
        $scope.currentPage = data.currentIndex;
        $scope.totalElement = data.totalElements;

    })

}).controller('BookAddController', function($scope, $rootScope, $stateParams,$state, Book) {
    $scope.book={};

    if($stateParams.id) {
        Book.get({id:$stateParams.id},function (data) {
            $scope.book = data;
        })
    }

    $scope.uploadFile = function ($index, $file) {
        console.log("clicked")
        $scope.$apply(function () {
            console.log($file)
            console.log($index)
            $scope.book.image  = $rootScope.setFile($file);
            console.log( $scope.book.image)
            // $scope.objects[$index].image  = $scope.attachment.file
            // $scope.objects[$index].fileContentType  = $scope.attachment.fileContentType
            // $scope.objects[$index].fileName  = $scope.attachment.fileName
            console.log($scope.attachments[$index])
        })

    };
    var onSaveSuccess = function (data) {
        $scope.globalMessage = "Commission Added Successfully";
        $state.go('commissions',null, {reload:true})
    };

    var onSaveError = function (result) {
        console.log(result);
        $state.formErrors = "Error Saving Chapter";
    };
    $scope.save = function() {
        console.log($scope.book)
        Book.save($scope.book, onSaveSuccess, onSaveError);
    };
});

