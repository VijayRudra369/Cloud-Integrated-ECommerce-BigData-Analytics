import java.io.IOException;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class ProductSales {

    // Mapper: reads each CSV row and sends
    // Product -> Quantity × Price
    public static class SalesMapper
            extends Mapper<Object, Text, Text, DoubleWritable> {

        private Text product = new Text();
        private DoubleWritable sales = new DoubleWritable();

        public void map(Object key, Text value, Context context)
                throws IOException, InterruptedException {

            String line = value.toString();

            // Skip the CSV header
            if (line.startsWith("Product,")) {
                return;
            }

            String[] fields = line.split(",");

            // CSV columns:
            // 0 Product
            // 1 Category
            // 2 Quantity
            // 3 Price
            // 4 Date
            // 5 Customer
            // 6 City

            if (fields.length == 7) {
                String productName = fields[0];

                double quantity = Double.parseDouble(fields[2]);
                double price = Double.parseDouble(fields[3]);

                double totalSales = quantity * price;

                product.set(productName);
                sales.set(totalSales);

                context.write(product, sales);
            }
        }
    }

    // Reducer: adds all sales belonging to the same product
    public static class SalesReducer
            extends Reducer<Text, DoubleWritable, Text, DoubleWritable> {

        private DoubleWritable result = new DoubleWritable();

        public void reduce(Text key, Iterable<DoubleWritable> values,
                            Context context)
                throws IOException, InterruptedException {

            double total = 0;

            for (DoubleWritable value : values) {
                total += value.get();
            }

            result.set(total);
            context.write(key, result);
        }
    }

    // Driver: configures and runs the MapReduce job
    public static void main(String[] args)
            throws Exception {

        Configuration conf = new Configuration();

        Job job = Job.getInstance(conf, "Product Wise Sales");

        job.setJarByClass(ProductSales.class);

        job.setMapperClass(SalesMapper.class);
        job.setReducerClass(SalesReducer.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(DoubleWritable.class);

        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}