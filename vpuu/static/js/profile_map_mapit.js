// extend the default Wazimap ProfileMaps object to add mapit support
var is_print_cookie = false;

var cookies = document.cookie;
if (!cookies.includes('print')){
        
var BaseProfileMaps = ProfileMaps;
ProfileMaps = function() {
    var self = this;
    this.mapit_url = GeometryLoader.mapit_url;

    _.extend(this, new BaseProfileMaps());

    this.drawAllFeatures = function() {
        var self = this;
        var geo = this.geo;
        var geo_level = geo.this.geo_level;
        var geo_code = geo.this.geo_code;
        var geo_version = geo.this.version;

        // add demarcation boundaries
        if (geo_level == 'country') {
            this.map.setView({lat: -28.4796, lng: 10.698445}, 5);
        } else {
            // draw this geometry
            GeometryLoader.loadGeometryForGeo(geo_level, geo_code, geo_version, function(feature) {
                self.drawFocusFeature(feature);
            });
        }

        // peers
        var parents = _.keys(geo.parents);
        if (parents.length > 0) {
          self.drawSurroundingFeatures(geo_level, parents[0], null, geo_version);
        }

        // every ancestor up to just before the root geo
        for (var i = 0; i < parents.length-1; i++) {
          self.drawSurroundingFeatures(parents[i], parents[i+1], null, geo_version);
        }

        //Get the children geo shapefiles for muni level
        if (geo.this.child_level) {
	    if (geo_level == 'municipality'){
		drawControl(geo_code, geo_level, geo_version).then(function(result){
			console.log(result);
		    });     
		
	    }else{
		self.drawSurroundingFeatures(geo.this.child_level, geo_level, geo_code, geo_version);
	    }
          
        }
    };
    async function drawControl(geo_code, geo_level, geo_version){
	//var overlayMap = {};
	var layerControl = L.control.layers(null, null, {collapased: false}).addTo(self.map);
	await GeometryLoader.subPlaceLayers(geo_code, geo_level, geo_version, function(geojson){
	    var layer = self.drawGeoFeatures(geojson);
	    layerControl.addOverlay(layer, 'Subplace');
	});
	await GeometryLoader.wardLayers(geo_code, geo_level, geo_version, function(geojson){
	    var layer = self.drawGeoFeatures(geojson);
	    layerControl.addOverlay(layer, 'Ward');
	});
	await GeometryLoader.informalSettlementLayers(geo_code, geo_level, geo_version, function(geojson){
	    var layer = self.drawGeoFeatures(geojson);
	    layerControl.addOverlay(layer, 'Informal Settlement');
	});
	return 'complete';
    };

    this.drawGeoFeatures = function(features) {
        // draw all others
        return L.geoJson(features, {
            style: this.layerStyle,
            onEachFeature: function(feature, layer) {
                layer.bindLabel(feature.properties.name, {direction: 'auto'});

                layer.on('mouseover', function() {
                    layer.setStyle(self.hoverStyle);
                });
                layer.on('mouseout', function() {
                    layer.setStyle(self.layerStyle);
                });
                layer.on('click', function() {
                    window.location = '/profiles/' + feature.properties.level + '-' + feature.properties.code + '/';
                });
            },
        });
    };

    // Add map shapes for a level, limited to within the parent level (eg.
    // wards within a municipality).
    this.drawSurroundingFeatures = function(level, parent_level, parent_code, parent_version) {
        var code,
            parent,
            self = this,
            url;

        parent_code = parent_code || this.geo.parents[parent_level].geo_code;
        parent_version = parent_version || this.geo.parents[parent_level].geo_version;
        parent = MAPIT.level_codes[parent_level] + '-' + parent_code;

        // code of 'level', if any?
        if (this.geo.this.geo_level == level) {
            code = this.geo.this.geo_code;
        } else if (this.geo.parents[level]) {
            code = this.geo.parents[level].geo_code;
        }

        GeometryLoader.loadGeometrySet(parent + '|' + MAPIT.level_codes[level], level, parent_version, function(geojson) {
            // don't include this smaller geo, we already have a shape for that
            geojson.features = _.filter(geojson.features, function(f) {
                return f.properties.code != code;
            });

            self.drawFeatures(geojson);
        });

        // if we're loading districts, we also want to load metros, because
        // districts don't give us full coverage
        if (level == 'district') {
            GeometryLoader.loadGeometrySet(parent + '|' + MAPIT.level_codes.municipality, 'municipality', parent_version, function(geojson) {
                // only keep metros
                geojson.features = _.filter(geojson.features, function(f) {
                    // only metro codes are three letters
                    return f.properties.code.length == 3;
                });

                self.drawFeatures(geojson);
            });
        }
    };
};
};
