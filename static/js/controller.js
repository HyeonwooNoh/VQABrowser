//
var browserApp = angular.module('browserApp', ['ngCookies','ui.bootstrap']);
var dataList;

browserApp.controller('exampleCtrl', function ($scope, $http) {
   $scope.name = 'Hyeonwoo Noh';
   $scope.count = 0;
   $scope.init = function () {
      $scope.count = 0;
   };
   $scope.getValue = function () {
      $http.get("test").then(function (response) {
         $scope.value = response.data;
      });
   };
});

browserApp.controller('visualizeCtrl', function ($scope, $http, $cookieStore, $interval) {

   if (angular.isDefined($cookieStore.get('active'))){
      $scope.active = $cookieStore.get('active');
   } else {
      $scope.active = {};
      $scope.active.vis = true;
      $cookieStore.put('active', $scope.active);
   };
   var stop;
   $scope.progress_text = 'init';
   $scope.accuracy = $cookieStore.get('accuracy');
   if (angular.isDefined($cookieStore.get('wait'))){
      $scope.wait = $cookieStore.get('wait');
   } else {
      $scope.wait = false;
   };
   
   if (angular.isDefined($cookieStore.get('addshow'))){
      $scope.addshow = $cookieStore.get('addshow');
   } else {
      $scope.addshow = 0;
   };
   $scope.cacheadditional = function() {
      $scope.addshow = 1-$scope.addshow;
      $cookieStore.put('addshow', $scope.addshow); 
   };
   if (angular.isDefined($cookieStore.get('interpolation'))){
      $scope.interpolation = $cookieStore.get('interpolation');
   } else {
      $scope.interpolation = 'nointerpolation';
   };
   $scope.toggleinterpolation = function() {
     if ($scope.interpolation == 'nointerpolation') {
        $scope.interpolation = 'interpolation';
        $cookieStore.put('interpolation', $scope.interpolation);
     } else {
        $scope.interpolation = 'nointerpolation';
        $cookieStore.put('interpolation', $scope.interpolation);
     };
   };
   if (angular.isDefined($cookieStore.get('aspectratio'))){
      $scope.aspectratio = $cookieStore.get('aspectratio');
      $scope.imgclass = $cookieStore.get('imgclass');
   } else {
      $scope.aspectratio = 'rectimg';
      $scope.imgclass = {};
      $scope.imgclass.vis = 'visimg';
      $scope.imgclass.add = 'addimg';
   };
   $scope.toggleaspectratio = function() {
      if ($scope.aspectratio == 'sqimg') {
         $scope.aspectratio = 'rectimg'
         $scope.imgclass.vis = 'visimg';
         $scope.imgclass.add = 'addimg';
         $cookieStore.put('aspectratio', $scope.aspectratio);
         $cookieStore.put('imgclass', $scope.imgclass);
      } else {// $scope.aspectratio == 'rectimg';
         $scope.aspectratio = 'sqimg'
         $scope.imgclass.vis = 'sqvisimg';
         $scope.imgclass.add = 'sqaddimg';
         $cookieStore.put('aspectratio', $scope.aspectratio);
         $cookieStore.put('imgclass', $scope.imgclass);
      };
   };
   $scope.setadddir = function(param) {
      $scope.adddir = param;
   };
   $scope.setadditional = function(params) {
      $http({
        method: 'POST',
        url: '/setadditional',
        data: params.additionaldir
      }).then(function(response){
         $scope.adddir = response.data.adddir;
      });
   };
   $scope.oracle = function() {
      $http.get("getoraclemerge").then(function(response){
         $scope.evalres_fn = response.data.evalres_fn;
      });
   }; 
   $scope.set_oracle_active = function() {
      $scope.active = {}
      $scope.active.oracle = true;
      $cookieStore.put('active', $scope.active);
   };
   $scope.set_analyze_active = function() {
      $scope.active = {}
      $scope.active.analyze = true;
      $cookieStore.put('active', $scope.active);
   };
   $scope.analyzeprev = function() {
      $http.get("getanalyzeprev").then(function(response){
         $scope.scores_fn = response.data.scores_fn;
         $scope.scorelists = response.data.scorelists;
      });
   };
   $scope.analyzenext = function() {
      $http.get("getanalyzenext").then(function(response){
         $scope.scores_fn = response.data.scores_fn;
         $scope.scorelists = response.data.scorelists;
      });
   };
   $scope.analyze = function() {
      $http.get("getanalyze").then(function(response){
         $scope.scores_fn = response.data.scores_fn;
         $scope.scorelists = response.data.scorelists;
      });
   };
   $scope.set_vis_active = function() {
      $scope.active = {}
      $scope.active.vis = true;
      $cookieStore.put('active', $scope.active);
   };
   // function for visualization
   $scope.visualize = function() {
      $http.get("getvisdata").then(function (response) {
         $scope.visres = response.data.visres; 
      });
   };
   $scope.visnextdata = function() {
      $http.get("getnextdata").then(function (response) {
         $scope.visres = response.data.visres; 
      });
   };
   $scope.visprevdata = function() {
      $http.get("getprevdata").then(function (response) {
         $scope.visres = response.data.visres; 
      });
   };
   if (angular.isDefined($cookieStore.get('queryquestion'))){
      $scope.queryquestion = $cookieStore.get('queryquestion');
   } else {
      $scope.queryquestion = '';
   };
   $scope.showquestion = function(question) {
      $http({
        method: 'POST',
        url: '/showquestion',
        data: question
      }).then(function(response){
         $scope.visres = response.data.visres;
         $scope.active.vis = true;
      });
   }
   $scope.searchquestion = function(params) {
      $http({
        method: 'POST',
        url: '/searchquestion',
        data: params.searchq
      }).then(function(response){
         $scope.queryquestion = params.searchq;
         $scope.searchedlist = response.data.searchedlist;
         $cookieStore.put('queryquestion', $scope.queryquestion);
         $scope.qlist = '';
      });
   };
   $scope.searchpreview = function(params) {
      if (params.searchq.length == 0) {
        $scope.qlist = '';
        return;
      };
      $http({
        method: 'POST',
        url: '/searchpreview',
        data: params.searchq
      }).then(function(response){
         $scope.abc = response.data.result;
         $scope.qlist = response.data.qlist;
      });
      $scope.searchq = $scope.searchq + 'type';
   };
   $scope.set_questat_active = function() {
      $scope.active = {}
      $scope.active.questat = true;
      $cookieStore.put('active', $scope.active);
   };
   $scope.set_ques_active = function() {
      $scope.active = {}
      $scope.active.ques = true;
      $cookieStore.put('active', $scope.active);
   };
   $scope.getquestions = function() {
      $http.get("getquestions").then(function (response) {
         $scope.quenums = response.data.quenums;
      });
   };
   $scope.getnextquestions = function() {
      $http.get("getnextquestions").then(function (response) {
         $scope.quenums = response.data.quenums;
      });
   };
   $scope.getprevquestions = function() {
      $http.get("getprevquestions").then(function (response) {
         $scope.quenums = response.data.quenums;
      });
   };
   $scope.visquestion = function(que) {
      var visq = "visquestion/" + que.toString();
      $scope.seearg = visq;
      $http.get(visq).then(function (response) {
         $scope.visres = response.data.visres;
         $scope.active.vis = true;
      });
   };
   $scope.set_eval_active = function() {
      $scope.active = {}
      $scope.active.eval = true;
      $cookieStore.put('active', $scope.active);
   };
   // function for evaluation
   $scope.evaluate = function() {
      if (angular.isDefined(stop)) return;
      $scope.wait = true;
      $cookieStore.put('wait', $scope.wait);
      $scope.evaluated = false;
      $http.get("getscore").then(function (response) {
         var accresp = response.data;
         $scope.accuracyfn = accresp.fn;
         $scope.accuracy = accresp.accuracy;
         $cookieStore.put('accuracy', $scope.accuracy);
         $scope.wait = false;
         $cookieStore.put('wait', $scope.wait);
         $scope.evaluated = true;
      });
      $scope.progress_check();
   };
   $scope.progress_check = function() {
      if (angular.isDefined(stop)) return;
      stop = $interval(function() {
         var evalstate;
         $http.get("evalprogress").then(function (response) {
            var isprocessing = response.data.processing;
            var progress_text = response.data.text;
            if (isprocessing == true) {
               $scope.isprocessing = isprocessing;
               $scope.progress_text = progress_text;
            } else {
               $scope.isprocessing = isprocessing;
               $scope.progress_text = 'done';
               $scope.stop_checking();
            }
         });
      }, 1000); 
   };
   $scope.stop_checking = function() {
      if (angular.isDefined(stop)) {
         $interval.cancel(stop);
         stop = undefined;
      }
   };
   $scope.$on('$destroy', function() {
      // Make sure that the interval is destroyed too
      $scope.stop_checking();
   });

});


