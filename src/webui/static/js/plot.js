var margin = {top: 30, right: 20, bottom: 30, left: 50};
var width = 600 - margin.left - margin.right,
    height = 400 - margin.top - margin.bottom;
    
var svg = d3.select("div#plot")
   .append("div")
   .classed("svg-container", true) //container class to make it responsive
   .append("svg")
   //responsive SVG needs these 2 attributes and no width and height attr
   .attr("preserveAspectRatio", "xMinYMin meet")
   .attr("viewBox", "0 0 600 400")
   //class to make it responsive
   .classed("svg-content-responsive", true);

var x = d3.scaleLinear().range([0, width]);
var y = d3.scaleLinear().range([height, 0]);

var xAxis = d3.axisBottom(x)
var yAxis = d3.axisLeft(y)
    
var valueline = d3.line()
    .x(function(d) { return x(d.time); })
    .y(function(d) { return y(d.temperature); });

d3.json("measurement", function(error, data) {
    if (error) {
        return;
    }

    var reference = data.reference
    var measurement = data.measurement
    
    x.domain([0, d3.max(reference, function(d) { return d.time; })]);
    y.domain([15, 70]);
    
    svg.append("path")
        .attr("class", "measurement")
        .attr("d", valueline(measurement));
        
    svg.append("path")
        .attr("class", "reference")
        .attr("d", valueline(reference));
    
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis);
        
    svg.append("text")
        .attr("x", width / 2)
        .attr("y", height + margin.bottom)
        .style("text-anchor", "middle")
        .text("Zeit [Minuten]");
        
    svg.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - margin.left)
        .attr("x",0 - (height / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text("Temperatur [°C]");
});
