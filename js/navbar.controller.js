'use strict';

angular.module('app')
    .controller('NavbarController', function ($scope, $location, $state) {
        //$scope.isAuthenticated=false;
         $scope.isAuthenticated = true;
         $scope.$state = $state;

        $scope.username='Account';

    });
