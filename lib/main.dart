import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:google_maps_flutter/google_maps_flutter.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Land Survey App',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      debugShowCheckedModeBanner: false,
      home: const MapScreen(),
    );
  }
}

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  // Controller for the map
  GoogleMapController? _mapController;
  // Controller for the search text field
  final TextEditingController _searchController = TextEditingController();
  // The set of polygons to display on the map
  final Set<Polygon> _polygons = {};

  // Initial camera position (Chicago, IL, where the sample data is)
  static const CameraPosition _initialCameraPosition = CameraPosition(
    target: LatLng(41.881832, -87.623177),
    zoom: 16,
  );

  @override
  void initState() {
    super.initState();
    // In the next step, we'll load the plot data here.
    _loadPlotData();
  }

  // Loads plot data from the GeoJSON asset file.
  Future<void> _loadPlotData() async {
    final String geoJsonString = await rootBundle.loadString('assets/sample_plots.geojson');
    final Map<String, dynamic> geoJson = json.decode(geoJsonString);
    final List<dynamic> features = geoJson['features'];

    final Set<Polygon> loadedPolygons = {};

    for (final feature in features) {
      final geometry = feature['geometry'];
      if (geometry['type'] == 'Polygon') {
        // GeoJSON coordinates are in (longitude, latitude) order.
        // The Polygon object expects a list of LatLng objects.
        final List<dynamic> coordinates = geometry['coordinates'][0]; // Assumes single-ring polygons
        final List<LatLng> points = coordinates
            .map((coord) => LatLng(coord[1], coord[0])) // Create LatLng, swapping order
            .toList();

        final String polygonId = 'polygon_${loadedPolygons.length}';

        loadedPolygons.add(
          Polygon(
            polygonId: PolygonId(polygonId),
            points: points,
            strokeWidth: 2,
            strokeColor: Colors.red,
            fillColor: Colors.red.withOpacity(0.3),
            consumeTapEvents: true,
            onTap: () {
              // Optional: show info when a polygon is tapped
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Owner: ${feature['properties']['owner']}'),
                  duration: const Duration(seconds: 2),
                ),
              );
            },
          ),
        );
      }
    }

    if (mounted) {
      setState(() {
        _polygons.addAll(loadedPolygons);
      });
    }
  }

  // Handles the search functionality.
  void _handleSearch() {
    final String query = _searchController.text.toLowerCase();
    if (query.isEmpty) {
      return;
    }

    // --- SIMULATED GEOCODING ---
    // In a real application, you would use a geocoding service (like Google's)
    // to convert the address `query` into latitude and longitude coordinates.
    // For this demo, we'll just check for the names of the owners in our sample data.

    LatLng? targetLocation;
    if (query.contains("jules verne")) {
      // Coordinates for the first plot
      targetLocation = const LatLng(41.881832, -87.623177);
    } else if (query.contains("h.g. wells")) {
      // Coordinates for the second plot
      targetLocation = const LatLng(41.881000, -87.624000);
    }

    if (targetLocation != null) {
      _mapController?.animateCamera(
        CameraUpdate.newCameraPosition(
          CameraPosition(
            target: targetLocation,
            zoom: 18, // Zoom in closer to the specific plot
          ),
        ),
      );
    } else {
      // If the address is not found in our simple simulation
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("Address not found. Try 'Jules Verne' or 'H.G. Wells'."),
          duration: Duration(seconds: 3),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Land Plot Viewer'),
        backgroundColor: Colors.blue.shade700,
      ),
      body: Stack(
        children: [
          GoogleMap(
            initialCameraPosition: _initialCameraPosition,
            onMapCreated: (controller) {
              _mapController = controller;
            },
            polygons: _polygons,
            mapType: MapType.hybrid, // Start with a satellite/road hybrid view
          ),
          Positioned(
            top: 10,
            left: 10,
            right: 10,
            child: Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
                boxShadow: const [
                  BoxShadow(
                    color: Colors.black26,
                    blurRadius: 10,
                    offset: Offset(0, 2),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _searchController,
                      decoration: const InputDecoration(
                        hintText: 'Search by address or GPS...',
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(horizontal: 15),
                      ),
                      onSubmitted: (_) => _handleSearch(),
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.search),
                    onPressed: _handleSearch,
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
