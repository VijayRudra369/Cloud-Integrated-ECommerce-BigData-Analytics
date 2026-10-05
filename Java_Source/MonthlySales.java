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

public class MonthlySales {

    public static class SalesMapper
            extends Mapper<Object, Text, Text, DoubleWritable> {

        private Text month = new Text();
        private DoubleWritable sales = new DoubleWritable();

        public void map(Object key, Text value, Context context)
                throws IOException, InterruptedException {

            String line = value.toString();

            if (line.startsWith("Product,")) {
                return;
            }

            String[] fields = line.split(",");

            if (fields.length == 7) {

                String date = fields[4];

                // Date format: YYYY-MM-DD
                String monthName = date.substring(0, 7);

                double quantity = Double.parseDouble(fields[2]);
                double price = Double.parseDouble(fields[3]);

                double totalSales = quantity * price;

                month.set(monthName);
                sales.set(totalSales);

                context.write(month, sales);
            }
        }
    }

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

    public static void main(String[] args)
            throws Exception {

        Configuration conf = new Configuration();

        Job job = Job.getInstance(conf, "Monthly Sales");

        job.setJarByClass(MonthlySales.class);

        job.setMapperClass(SalesMapper.class);
        job.setReducerClass(SalesReducer.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(DoubleWritable.class);

        FileInputFormat.addInputPath(
                job, new Path(args[0]));

        FileOutputFormat.setOutputPath(
                job, new Path(args[1]));

        System.exit(
                job.waitForCompletion(true) ? 0 : 1);
    }
}