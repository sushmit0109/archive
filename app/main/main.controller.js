'use strict';

angular.module('app')
    .controller('MainController', function ($scope, $rootScope, $anchorScroll, $stateParams , $state, AllBook) {
        $scope.time = 0;
        $scope.total = 0;
        $scope.page = 0;
        $scope.per_page = 20;
        $scope.jobs = [];
        $scope.cats = [];

        $rootScope.focusById = function (id) {
                if($state.current !=='home') {
                        $state.go('home', {tid:id},{reload:true})
                }
                $anchorScroll(id);
        };

        if($stateParams.tid) {
                $anchorScroll($stateParams.tid);
        }

        AllBook.get(function (data) {
                $scope.books = data;
        })


    });
